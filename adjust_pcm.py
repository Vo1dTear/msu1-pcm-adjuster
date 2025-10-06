import struct
import sys
import math

def adjust_pcm_volume(infile, outfile, factor):
    with open(infile, "rb") as fin:
        header = fin.read(8)  # "MSU1" + loop offset (4 bytes)
        pcm_data = fin.read()

    # convert to 16-bit little endian samples
    samples = struct.unpack("<" + "h" * (len(pcm_data) // 2), pcm_data)

    # apply factor with clipping
    adjusted = [max(min(int(s * factor), 32767), -32768) for s in samples]

    # repack into binary
    new_pcm_data = struct.pack("<" + "h" * len(adjusted), *adjusted)

    with open(outfile, "wb") as fout:
        fout.write(header)       # keep header intact
        fout.write(new_pcm_data) # write adjusted samples


if __name__ == "__main__":
    if len(sys.argv) < 2 or "--help" in sys.argv or "-h" in sys.argv:
        print("""
PCM Volume Adjuster (single file)

Usage:
  python adjust_pcm.py input.pcm output.pcm factor
    - Adjust volume using a linear factor (1.0 = original volume).

  python adjust_pcm.py input.pcm output.pcm --db <value>
    - Adjust volume using decibels (dB). Example: --db -3

Examples:
  python adjust_pcm.py audio.pcm audio_lower.pcm 0.75
  python adjust_pcm.py audio.pcm audio_louder.pcm --db 3
""")
        sys.exit(0)

    infile = sys.argv[1]
    outfile = sys.argv[2]

    # Linear factor mode
    if len(sys.argv) == 4:
        if sys.argv[3].startswith("--db"):
            print("❌ Invalid usage. Correct: --db <value>")
            sys.exit(1)
        factor = float(sys.argv[3])
    # Decibel mode
    elif len(sys.argv) == 5 and sys.argv[3] == "--db":
        db_value = float(sys.argv[4])
        factor = 10 ** (db_value / 20)
    else:
        print("❌ Invalid arguments. Use --help for usage instructions.")
        sys.exit(1)

    adjust_pcm_volume(infile, outfile, factor)
