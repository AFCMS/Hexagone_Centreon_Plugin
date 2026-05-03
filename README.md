 # Hexagone Centreon Plugin

A Centreon/Nagios-compatible monitoring plugin written in Python, providing
HTTP endpoint checks and system resource checks (CPU, memory, disk).

## Requirements

- Python 3.10+
- `psutil` (for CPU/memory/disk modes)

```bash
pip install -r requirements.txt
```

## Usage

```
check_hexagone.py <mode> [options]
```

### Modes

| Mode     | Description                             |
|----------|-----------------------------------------|
| `http`   | Check an HTTP/HTTPS endpoint            |
| `cpu`    | Check CPU usage                         |
| `memory` | Check memory (RAM) usage                |
| `disk`   | Check disk space usage                  |

### Exit codes

| Code | Status   |
|------|----------|
| 0    | OK       |
| 1    | WARNING  |
| 2    | CRITICAL |
| 3    | UNKNOWN  |

---

### `http` — HTTP/HTTPS endpoint check

```
check_hexagone.py http -U <URL> [-e <code>] [-s <string>] [-w <ms>] [-c <ms>] [-t <sec>]
```

| Option | Long             | Description                                       |
|--------|------------------|---------------------------------------------------|
| `-U`   | `--url`          | URL to check (required)                           |
| `-e`   | `--expected-code`| Expected HTTP status code (default: 200)          |
| `-s`   | `--string`       | String that must appear in the response body      |
| `-w`   | `--warning`      | Warning threshold for response time (ms)          |
| `-c`   | `--critical`     | Critical threshold for response time (ms)         |
| `-t`   | `--timeout`      | Connection timeout in seconds (default: 10)       |

**Examples:**

```bash
# Check that a URL returns HTTP 200
./check_hexagone.py http -U https://example.com

# Warn if response > 500 ms, critical if > 2000 ms
./check_hexagone.py http -U https://example.com -w 500 -c 2000

# Verify a specific string appears in the response
./check_hexagone.py http -U https://example.com -s "Welcome"
```

**Sample output:**

```
OK - HTTP 200 - 142ms response time (OK) | 'response_time'=142.35ms;500;2000;0
```

---

### `cpu` — CPU usage check

```
check_hexagone.py cpu [-w <pct>] [-c <pct>] [--per-cpu]
```

| Option      | Long          | Description                                         |
|-------------|---------------|-----------------------------------------------------|
| `-w`        | `--warning`   | Warning threshold in % (default: 80)                |
| `-c`        | `--critical`  | Critical threshold in % (default: 95)               |
|             | `--per-cpu`   | Report usage per CPU core in addition to average    |

**Example:**

```bash
./check_hexagone.py cpu -w 80 -c 95
```

**Sample output:**

```
OK - CPU usage: 23.4% | 'cpu'=23.4%;80;95;0;100
```

---

### `memory` — Memory (RAM) usage check

```
check_hexagone.py memory [-w <pct>] [-c <pct>]
```

| Option | Long          | Description                              |
|--------|---------------|------------------------------------------|
| `-w`   | `--warning`   | Warning threshold in % (default: 80)     |
| `-c`   | `--critical`  | Critical threshold in % (default: 95)    |

**Example:**

```bash
./check_hexagone.py memory -w 80 -c 95
```

**Sample output:**

```
OK - Memory usage: 54.2% (4396 MB used / 8192 MB total, 3796 MB available) | 'memory_used'=4396.0MB;; 'memory_used_pct'=54.2%;80;95;0;100
```

---

### `disk` — Disk space usage check

```
check_hexagone.py disk [-p <path>] [-w <pct>] [-c <pct>]
```

| Option | Long          | Description                                   |
|--------|---------------|-----------------------------------------------|
| `-p`   | `--path`      | Mount point or path to check (default: `/`)   |
| `-w`   | `--warning`   | Warning threshold in % (default: 80)          |
| `-c`   | `--critical`  | Critical threshold in % (default: 90)         |

**Example:**

```bash
./check_hexagone.py disk -p / -w 80 -c 90
```

**Sample output:**

```
OK - Disk usage on /: 41.3% (82.6 GB used / 200.0 GB total, 117.4 GB free) | 'disk_used'=82.6GB;; 'disk_used_pct'=41.3%;80;90;0;100
```

---

## Project structure

```
check_hexagone.py       # Main entry point
hexagone/
  plugin.py             # Base plugin framework (exit codes, thresholds, perfdata)
  modes/
    http.py             # HTTP/HTTPS check mode
    cpu.py              # CPU usage check mode
    memory.py           # Memory usage check mode
    disk.py             # Disk space check mode
tests/
  test_plugin.py        # Unit tests for base framework
  test_http.py          # Unit tests for HTTP mode
  test_modes.py         # Unit tests for CPU/memory/disk modes
requirements.txt
```

## Running tests

```bash
pip install psutil pytest
python -m pytest tests/ -v
```
