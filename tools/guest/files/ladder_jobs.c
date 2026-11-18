/*
 * Copyright (c) 2026 Mario Andres Munoz
 * Distributed under the terms of the MIT License. See LICENSE.
 *
 * Rung 1 reference jobs of the ladder (docs/decisions/012-resume-s2-s3.md).
 * GL ES 3.2 compute jobs with no window system, each checked against the CPU:
 *   copy        glCopyBufferSubData of 1 MiB
 *   add_f32     y[i] = a[i] + b[i]
 *   q8_0        mul_mat_vec_q8_0: ggml block_q8_0 rows (34 bytes per 32 values)
 *               times an FP32 vector, same operation order as the host probe
 *               haiku-k40c-llm tools/probes/nvc0_compile_probe.c
 *   matmul      C = A * B, FP32, N x N, timed (rung 6 Linux baseline)
 * The CPU reference uses fmaf in the order of the shaders. The inputs make
 * every product exact (add_f32 and matmul: values on a 2^-12 grid;
 * q8_0: x on a 2^-7 grid and 4-bit scales, block sums of at most 23 bits),
 * so a fused or a separate multiply-add gives the same bits, and a correct
 * GPU result is bit-identical. The log gives the count of
 * different words and the largest relative error for each job.
 *
 * Build: cc -O2 -o ladder_jobs ladder_jobs.c -lEGL -lGLESv2 -lgbm -lm
 * Run:   ./ladder_jobs [MATMUL_N]     (default 1024, a multiple of 16)
 * Exit status 0 = every job is bit-identical to the CPU.
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl32.h>
#include <gbm.h>

#define ADD_N (1 << 16)
#define Q8_ROWS 512
#define Q8_COLS 4096
#define Q8_BLOCK 34
#define REPEATS 10

static const char* kAdd =
	"#version 320 es\n"
	"layout(local_size_x = 64) in;\n"
	"layout(std430, binding = 0) readonly buffer A { float v[]; } a;\n"
	"layout(std430, binding = 1) readonly buffer B { float v[]; } b;\n"
	"layout(std430, binding = 2) writeonly buffer Y { float v[]; } y;\n"
	"uniform uint n;\n"
	"void main() {\n"
	"	uint i = gl_GlobalInvocationID.x;\n"
	"	if (i < n) y.v[i] = a.v[i] + b.v[i];\n"
	"}\n";

// One thread per row. The weights are a byte array read as words, because
// a 34-byte block is not word aligned.
static const char* kQ8 =
	"#version 320 es\n"
	"layout(local_size_x = 64) in;\n"
	"layout(std430, binding = 0) readonly buffer W { uint w[]; } w;\n"
	"layout(std430, binding = 1) readonly buffer X { float v[]; } x;\n"
	"layout(std430, binding = 2) writeonly buffer Y { float v[]; } y;\n"
	"uniform uint ncols;\n"
	"uniform uint nrows;\n"
	"uniform uint rowBytes;\n"
	"uint byteAt(uint o) { return (w.w[o >> 2u] >> ((o & 3u) * 8u)) & 0xffu; }\n"
	"void main() {\n"
	"	uint row = gl_GlobalInvocationID.x;\n"
	"	if (row >= nrows) return;\n"
	"	uint base = row * rowBytes;\n"
	"	float sum = 0.0;\n"
	"	for (uint k = 0u; k < (ncols >> 5u); k++) {\n"
	"		uint blk = base + k * 34u;\n"
	"		float d = unpackHalf2x16(byteAt(blk) | (byteAt(blk + 1u) << 8u)).x;\n"
	"		float acc = 0.0;\n"
	"		for (uint j = 0u; j < 32u; j++) {\n"
	"			int q = int(byteAt(blk + 2u + j) << 24u) >> 24;\n"
	"			acc = fma(float(q), x.v[k * 32u + j], acc);\n"
	"		}\n"
	"		sum = fma(d, acc, sum);\n"
	"	}\n"
	"	y.v[row] = sum;\n"
	"}\n";

// Naive 16 x 16 tiled product without shared memory: each thread reads one
// row of A and one column of B. The aim is a fixed, simple reference.
static const char* kMatmul =
	"#version 320 es\n"
	"layout(local_size_x = 16, local_size_y = 16) in;\n"
	"layout(std430, binding = 0) readonly buffer A { float v[]; } a;\n"
	"layout(std430, binding = 1) readonly buffer B { float v[]; } b;\n"
	"layout(std430, binding = 2) writeonly buffer C { float v[]; } c;\n"
	"uniform uint n;\n"
	"void main() {\n"
	"	uint col = gl_GlobalInvocationID.x;\n"
	"	uint row = gl_GlobalInvocationID.y;\n"
	"	float acc = 0.0;\n"
	"	for (uint k = 0u; k < n; k++)\n"
	"		acc = fma(a.v[row * n + k], b.v[k * n + col], acc);\n"
	"	c.v[row * n + col] = acc;\n"
	"}\n";

static uint32_t sState = 0x9E3779B9u;

// Fixed xorshift generator: the inputs are the same on every run.
static uint32_t
next(void)
{
	sState ^= sState << 13;
	sState ^= sState >> 17;
	sState ^= sState << 5;
	return sState;
}

// Uniform value in [-1, 1) on a 2^-12 grid.
static float
value(void)
{
	return (float)((int32_t)(next() >> 19) - 4096) / 4096.0f;
}

// Uniform value in [-1, 1) on a 2^-7 grid.
static float
coarse(void)
{
	return (float)((int32_t)(next() >> 24) - 128) / 128.0f;
}

static double
now(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec + t.tv_nsec * 1e-9;
}

static int
compare(const char* name, const float* gpu, const float* cpu, size_t n)
{
	size_t bad = 0;
	double worst = 0;
	for (size_t i = 0; i < n; i++) {
		if (memcmp(&gpu[i], &cpu[i], 4) != 0)
			bad++;
		double scale = fabs(cpu[i]) > 1e-30 ? fabs(cpu[i]) : 1.0;
		double e = fabs((double)gpu[i] - cpu[i]) / scale;
		if (!(e <= worst))
			worst = e;
	}
	printf("%s: elements %zu, different %zu, max relative error %.3g, %s\n",
		name, n, bad, worst, bad == 0 ? "PASS" : "FAIL");
	return bad == 0 ? 0 : 1;
}

static GLuint
program(const char* source)
{
	GLuint shader = glCreateShader(GL_COMPUTE_SHADER);
	GLint ok = 0;
	char log[2048] = "";
	glShaderSource(shader, 1, &source, NULL);
	glCompileShader(shader);
	glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
	if (!ok) {
		glGetShaderInfoLog(shader, sizeof(log), NULL, log);
		printf("FAIL: shader: %s\n", log);
		exit(2);
	}
	GLuint prog = glCreateProgram();
	glAttachShader(prog, shader);
	glLinkProgram(prog);
	glGetProgramiv(prog, GL_LINK_STATUS, &ok);
	if (!ok) {
		glGetProgramInfoLog(prog, sizeof(log), NULL, log);
		printf("FAIL: link: %s\n", log);
		exit(2);
	}
	return prog;
}

static GLuint
buffer(GLuint binding, const void* data, size_t bytes)
{
	GLuint b;
	glGenBuffers(1, &b);
	glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding, b);
	glBufferData(GL_SHADER_STORAGE_BUFFER, bytes, data,
		data != NULL ? GL_STATIC_DRAW : GL_DYNAMIC_READ);
	return b;
}

static void
readBack(GLuint b, void* out, size_t bytes)
{
	glBindBuffer(GL_SHADER_STORAGE_BUFFER, b);
	void* map = glMapBufferRange(GL_SHADER_STORAGE_BUFFER, 0, bytes,
		GL_MAP_READ_BIT);
	if (map == NULL || glGetError() != GL_NO_ERROR) {
		printf("FAIL: cannot read a buffer\n");
		exit(2);
	}
	memcpy(out, map, bytes);
	glUnmapBuffer(GL_SHADER_STORAGE_BUFFER);
}

static int
jobCopy(void)
{
	const size_t words = (1 << 20) / 4;
	uint32_t* src = malloc(words * 4);
	uint32_t* dst = malloc(words * 4);
	for (size_t i = 0; i < words; i++)
		src[i] = next();
	GLuint b[2];
	glGenBuffers(2, b);
	glBindBuffer(GL_COPY_READ_BUFFER, b[0]);
	glBufferData(GL_COPY_READ_BUFFER, words * 4, src, GL_STATIC_DRAW);
	glBindBuffer(GL_COPY_WRITE_BUFFER, b[1]);
	glBufferData(GL_COPY_WRITE_BUFFER, words * 4, NULL, GL_DYNAMIC_READ);
	glCopyBufferSubData(GL_COPY_READ_BUFFER, GL_COPY_WRITE_BUFFER, 0, 0,
		words * 4);
	glFinish();
	readBack(b[1], dst, words * 4);
	size_t bad = 0;
	for (size_t i = 0; i < words; i++)
		bad += dst[i] != src[i];
	printf("copy: bytes %zu, different words %zu, %s\n", words * 4, bad,
		bad == 0 ? "PASS" : "FAIL");
	free(src);
	free(dst);
	return bad == 0 ? 0 : 1;
}

static int
jobAdd(void)
{
	float* a = malloc(ADD_N * 4);
	float* b = malloc(ADD_N * 4);
	float* y = malloc(ADD_N * 4);
	float* ref = malloc(ADD_N * 4);
	for (int i = 0; i < ADD_N; i++) {
		a[i] = value() * 1000.0f;
		b[i] = value();
		ref[i] = a[i] + b[i];
	}
	GLuint prog = program(kAdd);
	buffer(0, a, ADD_N * 4);
	buffer(1, b, ADD_N * 4);
	GLuint out = buffer(2, NULL, ADD_N * 4);
	glUseProgram(prog);
	glUniform1ui(glGetUniformLocation(prog, "n"), ADD_N);
	glDispatchCompute(ADD_N / 64, 1, 1);
	glMemoryBarrier(GL_BUFFER_UPDATE_BARRIER_BIT);
	glFinish();
	readBack(out, y, ADD_N * 4);
	int rc = compare("add_f32", y, ref, ADD_N);
	free(a);
	free(b);
	free(y);
	free(ref);
	return rc;
}

// IEEE half-precision bits of a value that is exact in half precision.
static uint16_t
half(float f)
{
	uint32_t u;
	memcpy(&u, &f, 4);
	uint32_t sign = (u >> 16) & 0x8000u;
	int exp = (int)((u >> 23) & 0xff) - 127 + 15;
	uint32_t man = (u >> 13) & 0x3ffu;
	return (uint16_t)(sign | ((uint32_t)exp << 10) | man);
}

static int
jobQ8(void)
{
	const unsigned nb = Q8_COLS / 32;
	const unsigned rowBytes = nb * Q8_BLOCK;
	size_t wBytes = (size_t)Q8_ROWS * rowBytes;
	uint8_t* w = calloc((wBytes + 3) & ~(size_t)3, 1);
	float* x = malloc(Q8_COLS * 4);
	float* y = malloc(Q8_ROWS * 4);
	float* ref = malloc(Q8_ROWS * 4);
	for (unsigned c = 0; c < Q8_COLS; c++)
		x[c] = coarse();
	for (unsigned r = 0; r < Q8_ROWS; r++) {
		float sum = 0.0f;
		for (unsigned k = 0; k < nb; k++) {
			uint8_t* blk = w + (size_t)r * rowBytes + k * Q8_BLOCK;
			// Scale (1 + m/8) * 2^-e, e in 4..13: a normal half value.
			float m = (float)(next() & 7) / 8.0f;
			int e = (int)(next() % 10) + 4;
			float d = ldexpf(1.0f + m, -e);
			uint16_t h = half(d);
			blk[0] = h & 0xff;
			blk[1] = h >> 8;
			float acc = 0.0f;
			for (unsigned j = 0; j < 32; j++) {
				int8_t q = (int8_t)(next() >> 24);
				blk[2 + j] = (uint8_t)q;
				acc = fmaf((float)q, x[k * 32 + j], acc);
			}
			sum = fmaf(d, acc, sum);
		}
		ref[r] = sum;
	}
	GLuint prog = program(kQ8);
	buffer(0, w, (wBytes + 3) & ~(size_t)3);
	buffer(1, x, Q8_COLS * 4);
	GLuint out = buffer(2, NULL, Q8_ROWS * 4);
	glUseProgram(prog);
	glUniform1ui(glGetUniformLocation(prog, "ncols"), Q8_COLS);
	glUniform1ui(glGetUniformLocation(prog, "nrows"), Q8_ROWS);
	glUniform1ui(glGetUniformLocation(prog, "rowBytes"), rowBytes);
	glDispatchCompute((Q8_ROWS + 63) / 64, 1, 1);
	glMemoryBarrier(GL_BUFFER_UPDATE_BARRIER_BIT);
	glFinish();
	readBack(out, y, Q8_ROWS * 4);
	int rc = compare("mul_mat_vec_q8_0", y, ref, Q8_ROWS);
	free(w);
	free(x);
	free(y);
	free(ref);
	return rc;
}

static int
cmpDouble(const void* a, const void* b)
{
	double x = *(const double*)a, y = *(const double*)b;
	return (x > y) - (x < y);
}

static int
jobMatmul(unsigned n)
{
	size_t count = (size_t)n * n;
	float* a = malloc(count * 4);
	float* b = malloc(count * 4);
	float* c = malloc(count * 4);
	float* ref = malloc(count * 4);
	for (size_t i = 0; i < count; i++) {
		a[i] = value();
		b[i] = value();
	}
	// CPU reference in the shader order: k ascending, one fma per step.
	double t0 = now();
	for (unsigned r = 0; r < n; r++)
		for (unsigned col = 0; col < n; col++) {
			float acc = 0.0f;
			for (unsigned k = 0; k < n; k++)
				acc = fmaf(a[(size_t)r * n + k], b[(size_t)k * n + col], acc);
			ref[(size_t)r * n + col] = acc;
		}
	double cpu = now() - t0;
	GLuint prog = program(kMatmul);
	buffer(0, a, count * 4);
	buffer(1, b, count * 4);
	GLuint out = buffer(2, NULL, count * 4);
	glUseProgram(prog);
	glUniform1ui(glGetUniformLocation(prog, "n"), n);
	// First dispatch: compile, upload and warm-up; not timed.
	glDispatchCompute(n / 16, n / 16, 1);
	glFinish();
	double t[REPEATS];
	for (int i = 0; i < REPEATS; i++) {
		double s = now();
		glDispatchCompute(n / 16, n / 16, 1);
		glFinish();
		t[i] = now() - s;
	}
	glMemoryBarrier(GL_BUFFER_UPDATE_BARRIER_BIT);
	readBack(out, c, count * 4);
	qsort(t, REPEATS, sizeof(double), cmpDouble);
	double median = 0.5 * (t[REPEATS / 2 - 1] + t[REPEATS / 2]);
	double flops = 2.0 * n * n * (double)n;
	printf("matmul_f32: n %u, median %.6f s (min %.6f, max %.6f) over %d, "
		"%.2f GFLOP/s; cpu reference %.3f s\n", n, median, t[0],
		t[REPEATS - 1], REPEATS, flops / median * 1e-9, cpu);
	char name[32];
	snprintf(name, sizeof(name), "matmul_f32_%u", n);
	int rc = compare(name, c, ref, count);
	free(a);
	free(b);
	free(c);
	free(ref);
	return rc;
}

int
main(int argc, char** argv)
{
	unsigned n = argc > 1 ? (unsigned)strtoul(argv[1], NULL, 10) : 1024;
	if (n == 0 || n % 16 != 0) {
		printf("FAIL: MATMUL_N must be a positive multiple of 16\n");
		return 2;
	}
	EGLDisplay dpy = EGL_NO_DISPLAY;
	const char* node = "/dev/dri/renderD128";
	int fd = open(node, O_RDWR | O_CLOEXEC);
	if (fd >= 0) {
		struct gbm_device* gbm = gbm_create_device(fd);
		if (gbm != NULL)
			dpy = eglGetPlatformDisplay(EGL_PLATFORM_GBM_KHR, gbm, NULL);
		printf("device: %s\n", node);
	}
	if (dpy == EGL_NO_DISPLAY) {
		dpy = eglGetPlatformDisplay(EGL_PLATFORM_SURFACELESS_MESA,
			EGL_DEFAULT_DISPLAY, NULL);
		printf("device: none (surfaceless)\n");
	}
	if (dpy == EGL_NO_DISPLAY || !eglInitialize(dpy, NULL, NULL)) {
		printf("FAIL: no EGL display\n");
		return 2;
	}
	static const EGLint cfgAttr[] = { EGL_SURFACE_TYPE, EGL_DONT_CARE,
		EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_NONE };
	static const EGLint ctxAttr[] = { EGL_CONTEXT_MAJOR_VERSION, 3,
		EGL_CONTEXT_MINOR_VERSION, 2, EGL_NONE };
	EGLConfig cfg;
	EGLint count = 0;
	eglBindAPI(EGL_OPENGL_ES_API);
	eglChooseConfig(dpy, cfgAttr, &cfg, 1, &count);
	EGLContext ctx = eglCreateContext(dpy, count > 0 ? cfg : NULL,
		EGL_NO_CONTEXT, ctxAttr);
	if (ctx == EGL_NO_CONTEXT
		|| !eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, ctx)) {
		printf("FAIL: no GL ES 3.2 context (EGL error 0x%x)\n", eglGetError());
		return 2;
	}
	printf("renderer: %s\nversion: %s\n", glGetString(GL_RENDERER),
		glGetString(GL_VERSION));
	int bad = jobCopy();
	bad += jobAdd();
	bad += jobQ8();
	bad += jobMatmul(n);
	printf("%s: %d of 4 jobs differ from the CPU\n", bad == 0 ? "PASS" : "FAIL",
		bad);
	return bad == 0 ? 0 : 1;
}
