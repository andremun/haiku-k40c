# S1A cardless native check — 2026-10-27

The KVM Haiku guest loaded the cardless probe and reported PASS.
The run used a disposable overlay of ~/haiku-vm/system.qcow2.
The command is in command.txt. The launcher configuration is in launch.json.
The source revision is cf5ee7a. hashes.txt records driver and guest-kernel hashes.
The guest kernel matches the raw kernel used by the cross-link installation.

The result is cardless Haiku OS evidence only. It proves nothing about the K40c.
No panic occurred. Devfs loaded the probe twice, and both loads passed.
