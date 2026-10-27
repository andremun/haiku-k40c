# S1DMAMODEL findings

- The source has materially different Type1/V2 unmap semantics. Reconsulted the
  recorded Linux v6.8 source at 1279-1426. Returned size is not a location bitmap.
- V2 may remove multiple whole records across holes. V1 may extend removal past
  the request or remove nothing when starting inside an original map. Unmatched
  aggregate results and failed unmaps invalidate coverage rather than guess ranges.
- The host ledger fixes launch/device/container/generation, requires successful
  backend setup and contiguous complete observations, and has bounded records/events.
  Map announcements and failed maps add no coverage. EBUSY/unmap/retry can be
  represented as ordinary observations without retrying any physical stage.
- Witnesses are immutable diagnostics, not provider tokens. GPA, IOVA and HVA are
  independent fields. Every later observation stales prior witnesses. No live
  mapping identity, authentication, visibility or hardware claim is supplied.
- Ten tests pass, including a seeded independent page-set oracle over 500 updates.
  All tests are synthetic and perform no ioctl, guest or device access.
- During this task the user explicitly approved hardware access. ADR 008 records
  that authorization for planned S1 stages on 04:00.0. Other safety/review/stop
  gates remain. This task remains host-only.
- Final make check exits 0. Repository checks, exact reference pins, source-bound
  reports and all host suites pass. Approval text/current design now points to
  ADR 008; historical task records retain the authorization state at their date.
