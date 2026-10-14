#!/usr/bin/env python3
"""Add a released IPA to source.json, the AltStore-format source KSign reads for updates.

    python3 scripts/add-version.py <released .ipa> <download URL> "<what's new>"

Version, build, minimum iOS and bundle ID come from the IPA's own Info.plist. The app must already have an
entry in source.json (name, icon, description); its newest version goes first, which is what KSign offers.
"""
import json, os, plistlib, sys, zipfile
from datetime import datetime, timezone

ipa, url, notes = sys.argv[1:4]
with zipfile.ZipFile(ipa) as z:
    name = next(n for n in z.namelist() if n.startswith("Payload/") and n.endswith(".app/Info.plist") and n.count("/") == 2)
    info = plistlib.loads(z.read(name))

path = os.path.join(os.path.dirname(__file__), "..", "source.json")
with open(path) as f:
    source = json.load(f)
app = next((a for a in source["apps"] if a["bundleIdentifier"] == info["CFBundleIdentifier"]), None)
if app is None:
    sys.exit(f"No app with bundle ID {info['CFBundleIdentifier']} in source.json; add its entry first.")

version = info.get("CFBundleShortVersionString", "1.0")
if any(v["version"] == version for v in app["versions"]):
    sys.exit(f"{app['name']} {version} is already in source.json.")
app["versions"].insert(0, {
    "version": version,
    "buildVersion": info.get("CFBundleVersion", "1"),
    "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "localizedDescription": notes,
    "downloadURL": url,
    "size": os.path.getsize(ipa),
    "minOSVersion": info.get("MinimumOSVersion", "26.0"),
})
with open(path, "w") as f:
    json.dump(source, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"Added {app['name']} {version}")
