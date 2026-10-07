/*
 * Copyright 2026 Mario Andrés Muñoz. Distributed under the terms of the MIT License.
 *
 * Reference compute job for milestone S3: output[i] = input[i] + 1 as a
 * GL ES 3.1 compute shader, with no window system. It prints the renderer,
 * so the log shows whether Nouveau (the K40c) or the software renderer
 * (llvmpipe) ran it. Exit status 0 = every element is correct.
 *
 * Build: cc -O2 -o compute_test compute_test.c -lEGL -lGLESv2 -lgbm
 * Run:   ./compute_test            (NV50_PROG_DEBUG=1 prints the GPU code)
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl31.h>
#include <gbm.h>

#define N 1024

static const char* kSource =
	"#version 310 es\n"
	"layout(local_size_x = 64) in;\n"
	"layout(std430, binding = 0) readonly buffer In { uint a[]; } inbuf;\n"
	"layout(std430, binding = 1) writeonly buffer Out { uint a[]; } outbuf;\n"
	"void main() {\n"
	"	uint i = gl_GlobalInvocationID.x;\n"
	"	outbuf.a[i] = inbuf.a[i] + 1u;\n"
	"}\n";

int
main(void)
{
	static GLuint in[N], out[N];
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
		EGL_CONTEXT_MINOR_VERSION, 1, EGL_NONE };
	EGLConfig cfg;
	EGLint count = 0;
	eglBindAPI(EGL_OPENGL_ES_API);
	eglChooseConfig(dpy, cfgAttr, &cfg, 1, &count);
	EGLContext ctx = eglCreateContext(dpy, count > 0 ? cfg : NULL,
		EGL_NO_CONTEXT, ctxAttr);
	if (ctx == EGL_NO_CONTEXT
		|| !eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, ctx)) {
		printf("FAIL: no GL ES 3.1 context (EGL error 0x%x)\n", eglGetError());
		return 2;
	}
	printf("renderer: %s\nversion: %s\n", glGetString(GL_RENDERER),
		glGetString(GL_VERSION));

	GLuint shader = glCreateShader(GL_COMPUTE_SHADER);
	GLint ok = 0;
	char log[1024] = "";
	glShaderSource(shader, 1, &kSource, NULL);
	glCompileShader(shader);
	glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
	GLuint prog = glCreateProgram();
	glAttachShader(prog, shader);
	glLinkProgram(prog);
	if (ok)
		glGetProgramiv(prog, GL_LINK_STATUS, &ok);
	if (!ok) {
		glGetShaderInfoLog(shader, sizeof(log), NULL, log);
		printf("FAIL: shader: %s\n", log);
		return 2;
	}

	for (int i = 0; i < N; i++)
		in[i] = 3u * (GLuint)i + 7u;
	GLuint buf[2];
	glGenBuffers(2, buf);
	glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, buf[0]);
	glBufferData(GL_SHADER_STORAGE_BUFFER, sizeof(in), in, GL_STATIC_DRAW);
	glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, buf[1]);
	glBufferData(GL_SHADER_STORAGE_BUFFER, sizeof(out), NULL, GL_DYNAMIC_READ);

	glUseProgram(prog);
	glDispatchCompute(N / 64, 1, 1);
	glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT);
	glFinish();

	void* map = glMapBufferRange(GL_SHADER_STORAGE_BUFFER, 0, sizeof(out),
		GL_MAP_READ_BIT);
	if (map == NULL || glGetError() != GL_NO_ERROR) {
		printf("FAIL: cannot read the output buffer\n");
		return 2;
	}
	memcpy(out, map, sizeof(out));

	int bad = 0;
	for (int i = 0; i < N; i++)
		bad += out[i] != in[i] + 1u;
	printf("elements: %d, wrong: %d\n%s\n", N, bad, bad == 0 ? "PASS" : "FAIL");
	return bad == 0 ? 0 : 1;
}
