# Jaguar Toolchain Setup — Native Windows

This file documents exactly how to reproduce the Gate 1 toolchain on a clean Windows machine.
**Binaries are not committed to this repository** (license terms require separate download).

---

## 1. RMAC Assembler v2.5.2

**Source:** https://rmac.sourceforge.io/  
**Direct download (Windows x64):**
```
https://sourceforge.net/projects/rmac/files/2.5.2/rmac-2.5.2-win64.zip
```

Install:
```powershell
# From jaguar-toolchain/
Expand-Archive rmac-2.5.2-win64.zip -DestinationPath bin\rmac-extract
Copy-Item bin\rmac-extract\rmac.exe bin\rmac.exe
```

Verify:
```powershell
.\bin\rmac.exe -h | Select-Object -First 3
# Expected: "Renamed Macro Assembler ... V2.5.2"
```

---

## 2. RLN Linker v1.7.7

**Source:** https://rmac.sourceforge.io/ (same project, companion linker)  
**Direct download (Windows x64):**
```
https://sourceforge.net/projects/rmac/files/rln/1.7.7/rln-1.7.7-win64.zip
```

Install:
```powershell
Expand-Archive rln-1.7.7-win64.zip -DestinationPath bin\rln-extract
Copy-Item bin\rln-extract\rln.exe bin\rln.exe
```

Verify:
```powershell
.\bin\rln.exe 2>&1 | Select-Object -First 6
# Expected: ASCII art banner + "Removable Linker" + version
```

---

## 3. Virtual Jaguar v2.1.3 R5

**Fork:** OldLincoln / Virtual Jaguar Rx  
**Source:** https://github.com/OldLincoln/virtualjaguar-rx  
**Release:** R5  
**Download:** https://github.com/OldLincoln/virtualjaguar-rx/releases/tag/R5

Download `VirtualJaguarRx-R5-win64.zip` (or equivalent), extract to `emulator/vjaguar/`.

Verify:
```powershell
# Launch — title bar should show "Virtual Jaguar v2.1.3 Rx"
Start-Process .\emulator\vjaguar\virtualjaguar.exe
```

No BIOS ROM required. Dismiss the warning dialog on first launch.

---

## 4. Build & Run

```powershell
cd jaguar-toolchain

# Assemble
.\bin\rmac.exe -fb -m68000 -o hello\hello.o hello\hello.s

# Link → ABS  (hardware / flash cart / skunkboard)
.\bin\rln.exe -a 802000 -e 802000 -o hello\hello.abs hello\hello.o

# Link → COF  (emulator)
.\bin\rln.exe -a 802000 -e 802000 -c -o hello\hello.cof hello\hello.o

# Open in emulator: Jaguar > Open File > hello\hello.cof
Start-Process .\emulator\vjaguar\virtualjaguar.exe
```

**Expected result:** solid blue screen at 59.9 FPS.

---

## Pinned versions

| Tool | Version | SHA-256 of Windows x64 binary |
|------|---------|-------------------------------|
| rmac.exe | 2.5.2 | *(record after download)* |
| rln.exe | 1.7.7 | *(record after download)* |
| virtualjaguar.exe | 2.1.3 R5 | *(record after download)* |
