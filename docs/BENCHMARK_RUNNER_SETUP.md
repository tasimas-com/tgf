# TGF dedicated benchmark runner — operator runbook

**Status:** repository-side preparation and fail-closed checks are implemented. The project owner approved a scope waiver on 2026-10-17; no physical runner is provisioned or enabled, and the nightly workflow remains gated.
> **Owner-approved scope waiver (2026-10-17):** P0.1.4.f.3 physical-host provisioning/validation and P0.1.4.f.4 runner registration/first-run acceptance are waived for the current project stage. This is an administrative scope decision, not evidence of hardware acceptance. No physical benchmark host, pinned-frequency setup, thermal validation, self-hosted runner, or dedicated-host benchmark result is claimed. Keep `TGF_BENCHMARK_RUNNER_READY` unset. If the waiver is reversed, every acceptance step below becomes mandatory before the nightly workflow may be enabled.


This runbook is the acceptance procedure for P0.1.4.f.3 and P0.1.4.f.4. A successful CMake build on a general-purpose hosted runner is not a substitute for a dedicated bare-metal machine with controlled CPU frequency and reviewed thermal behavior.

## 1. Acceptance requirements

The benchmark runner must satisfy every item below before it is registered or enabled:

- Dedicated physical Linux x86-64 machine. Do not use a VM, container, shared virtual machine, or GitHub-hosted ephemeral runner.
- Exclusive benchmark use during the scheduled window. No unrelated user workloads, cron jobs, package upgrades, backups, or background CI jobs may contend for the CPU.
- Linux CPUFreq exposes every CPU policy. Every policy must use the performance governor and have equal, positive scaling_min_freq and scaling_max_freq values.
- The chosen fixed frequency must be supported by the CPU and its driver for every policy. Record the selected kHz value per policy; do not assume that a frequency available on one policy is available on every policy.
- Cooling and power delivery must be adequate for sustained runs. Record sensor readings before and after a sustained CPU load, and confirm that thermal or power throttling does not change the benchmark regime.
- Firmware, BIOS, CPU microcode, kernel, operating system, compiler, CMake, Ninja, Python, and Git versions must be recorded.
- The final inventory JSON, the preflight output, and a first benchmark artifact must be inspected before enabling the GitHub Actions variable.

A performance governor and fixed min/max limits constrain the CPUFreq policy; they do not defeat thermal, current, or firmware protection. Thermal throttling must still be checked during sustained load.

## 2. Provision and identify the machine

Provision a dedicated bare-metal host from hardware you own or a provider that explicitly supplies dedicated physical hardware. Keep the provider order/asset record in your private operations records; do not commit credentials, access tokens, serial numbers, IP addresses, or private hostnames.

Use an x86-64 Linux installation compatible with the repository's CMake/Ninja workflow. Install at least:

- Git
- Python 3
- CMake 3.25 or newer
- Ninja
- A supported C++ compiler (GCC 15/16 is the current Linux CI target)
- The distribution's CPUFreq utilities and sensor tools, where supported

Check the architecture and virtualization status:

~~~sh
uname -m
systemd-detect-virt --vm
~~~

The first command must report x86_64 (or the equivalent amd64). The second must return its documented “no virtualization detected” status. An error, missing command, or unknown virtualization result is not acceptance evidence.

Inspect the actual CPU and firmware, without publishing serial numbers:

~~~sh
lscpu
cat /proc/cpuinfo
sudo dmidecode --type system --type baseboard --type bios
~~~

Record CPU model, package/core/thread topology, microcode, board/system product and firmware versions. Do not copy dmidecode output containing serial numbers or UUIDs into the public repository.

## 3. Pin every CPU-frequency policy

First inspect the active driver and every policy:

~~~sh
cpupower frequency-info
for policy in /sys/devices/system/cpu/cpufreq/policy*; do
    [ -d "$policy" ] || continue
    echo "=== $policy ==="
    for field in scaling_driver scaling_available_governors \
                 scaling_available_frequencies scaling_min_freq \
                 scaling_max_freq scaling_governor related_cpus affected_cpus; do
        [ -r "$policy/$field" ] && printf '%s: ' "$field" && cat "$policy/$field"
    done
done
~~~

Choose a target frequency that is supported by all exposed policies. It must be within each policy's hardware-reported minimum/maximum and, where the driver publishes a discrete list, must appear in that list. If there is no common supported target, stop and select different hardware/firmware settings; do not silently choose a different frequency for some cores.

Set the performance governor and equal minimum/maximum limits for every policy. cpupower is the preferred interface when its output confirms that it applied the settings to all policies. The target is supplied in kHz after inspection; this example intentionally has no guessed frequency:

~~~sh
read -r -p "Enter a frequency accepted by cpupower and supported by every policy: " TARGET_FREQ
sudo cpupower frequency-set --governor performance \
    --min "$TARGET_FREQ" --max "$TARGET_FREQ"
~~~

If the driver does not expose the required controls through cpupower, use the driver's documented interface. Do not blindly write a value copied from another CPU. When using the generic CPUFreq sysfs interface, respect the current min/max bounds and the driver's required update order; changing an upper limit before raising a lower bound (or vice versa) can be rejected. Verify every write by reading the policy files again.

Disable or configure competing power-management services (for example, desktop power profiles, laptop tuning services, or vendor agents) so they cannot overwrite the selected governor/limits. Make the configuration persistent across reboot using the distribution's supported mechanism, then reboot and repeat the full inspection. The benchmark must not depend on an interactive shell command that disappears after reboot.

The preflight is read-only:

~~~sh
python3 tools/check_benchmark_host.py --require-bare-metal
~~~

It must exit with code 0. It checks x86-64, rejects virtualization indicators or an unprovable VM status, and checks every discovered CPUFreq policy for performance plus equal positive min/max limits. It does not change settings.

## 4. Validate thermal stability and capture the inventory

Check that temperature sensors are visible through Linux thermal zones or hwmon:

~~~sh
sensors
find /sys/class/thermal -maxdepth 2 -type f \( -name type -o -name temp \) -print
find /sys/class/hwmon -maxdepth 2 -type f \( -name name -o -name 'temp*_input' \) -print
~~~

Capture a baseline at idle, run a representative sustained CPU workload for at least 15 minutes, then capture the same sensor readings again. Use manufacturer limits and platform telemetry to check for thermal/current throttling; there is no universal safe temperature number for every processor. Record the load tool/version, duration, ambient conditions if known, before/after/max temperatures, throttle indicators, and any firmware power-limit events. Do not accept a machine whose clock behavior changes materially because its cooling or power budget is inadequate.

Capture the machine-readable inventory:

~~~sh
python3 tools/collect_benchmark_host_inventory.py \
    --output benchmark-artifacts/host-inventory.json
~~~

The collector is read-only and standard-library-only. It records CPU identity/topology/microcode, visible memory, non-serial DMI/firmware fields, every exposed frequency policy, thermal-zone and hwmon readings, OS/kernel and selected tool versions, plus an allowlist of GitHub runner metadata. It deliberately excludes serial numbers, UUIDs, asset tags, tokens, usernames, and network addresses.

Review the JSON. It must show:

- host.architecture as x86_64;
- host.virtualization.detected as false;
- all frequency_policies[*].pinned as true;
- thermal readings or a documented external telemetry source;
- non-empty CPU, firmware, OS, and compiler/build-tool identities;
- no secrets or machine-unique serial identifiers.

The inventory is a point-in-time snapshot. Keep the separate sustained-load/thermal-validation record with the host acceptance evidence.

## 5. Register the repository-scoped runner

Only after Sections 1–4 pass:

1. In GitHub repository settings for tasimas-com/tgf, open Actions → Runners → New self-hosted runner and choose Linux x64.
2. Follow the displayed installation and registration commands on the dedicated host. Treat the registration token as a secret: enter it only in the host's terminal, never commit it or put it in workflow logs.
3. Add exactly these labels: self-hosted, linux, x64, tgf-benchmark-pinned.
4. Run the agent as a dedicated unprivileged OS account. The workflow must not receive sudo/root access. Keep the host free of deployment credentials and personal SSH keys. Restrict network access to what runner operation and dependency retrieval require.
5. Keep the runner repository-scoped to TGF. Do not attach it to unrelated repositories or broad organization runner groups.
6. Ensure the runner is online and its labels match exactly. Reboot once and confirm the service starts with the CPUFreq settings still pinned.

This is a public repository. Never add the self-hosted runner to untrusted pull-request workflows. The benchmark workflow is intentionally limited to scheduled/manual execution, has read-only repository permissions, and remains guarded by the repository Actions variable. Preserve those restrictions.

## 6. First-run acceptance and readiness gate

Before enabling the gate, review the host inventory and thermal validation records with the workflow definition. Then dispatch the TGF Nightly Benchmarks workflow manually.

The run must:

- land on the dedicated runner with the required four labels;
- pass tools/check_benchmark_host.py --require-bare-metal;
- upload host-inventory.json, host.txt, and benchmark-results.json;
- complete the release build and showcase benchmark without errors;
- produce a valid JSON benchmark report.

Download and inspect the first artifact. Confirm that the machine identity and CPUFreq settings match the reviewed inventory and that the benchmark report is complete. Record the run URL, artifact ID, compiler/build versions, CPUFreq policy, thermal-validation evidence, and benchmark report review.

Only after that first run passes should an administrator set the repository Actions variable:

~~~text
TGF_BENCHMARK_RUNNER_READY=true
~~~

If the host is rebooted, its CPU/firmware/kernel changes, or its thermal/frequency configuration changes, repeat the host preflight and inventory review. Keep the variable unset if any acceptance check fails.

## 7. Current state

The preflight unit tests and CI contract checks cover the software rules. The current coding environment is a virtualized container with no exposed CPUFreq policy or thermal sensor sysfs data; it is intentionally rejected. No dedicated physical machine, self-hosted runner, first benchmark artifact, or enabled repository variable is claimed yet. P0.1.4.f.3 and P0.1.4.f.4 remain open until the physical acceptance process above is completed.
