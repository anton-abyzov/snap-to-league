"""Run the ShellHacks demo end to end through the running app, the way an organizer would:

1. snap the group-stage whiteboard, save the league, publish to EasyChamp;
2. hours later, snap the knockout page into the same league, review what changed, publish again;
3. snap the midnight Smash bracket as its own league.

python scripts/demo_shellhacks.py [base_url] PIN   ->  prints every link, writes data/demo_shellhacks.json
"""
import json
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 2 else "http://localhost:8077"
PIN = sys.argv[-1]
out = {}


def run(samples, league_id=None, reader="google/gemini-3.8-flash"):
    data = {"samples": samples, "reader": reader}
    if league_id:
        data["leagueId"] = league_id
    job = httpx.post(f"{BASE}/api/jobs", data=data, timeout=60).json()
    for _ in range(180):
        job = httpx.get(f"{BASE}/api/jobs/{job['id']}").json()
        if job["status"] != "reading" and (not job.get("checking") or job["checking"].get("finished")):
            return job
        time.sleep(1)
    raise SystemExit("import did not finish")


def publish(name, job, league_id=None, matches=None):
    ex = job["extraction"]
    body = {"id": league_id, "name": name, "sport": ex["sport"], "teams": ex["teams"],
            "matches": matches if matches is not None else ex["matches"], "jobId": job["id"]}
    lg = httpx.post(f"{BASE}/api/leagues", json=body).json()
    pub = httpx.post(f"{BASE}/api/leagues/{lg['id']}/publish", headers={"x-publish-pin": PIN}, timeout=300).json()
    return lg, pub


def show(label, job):
    print(f"\n== {label}: {job['extraction']['competition']} | {len(job['extraction']['matches'])} games | "
          f"main read {job['seconds']} s, check {job.get('seconds_checked')} s | {job['photos'][0]['reader']} | {job.get('checking')}")
    for f in job["flags"]:
        print("   card:", f["source"], "-", f["message"][:110])


cup = "ShellHacks Panther Pit Break Cup · Demo"
g = run("shellhacks-groups")
show("groups", g)
lg, pub = publish(cup, g)
out["cup_board"] = f"{BASE}/l/{lg['id']}"
out["cup_publish_1"] = {"mode": pub["mode"], "status": pub.get("status"), "links": pub.get("links")}
print("published:", pub["mode"], pub.get("status"), pub.get("links"))

k = run("shellhacks-knockout", league_id=lg["id"])
show("knockouts", k)
print("   changes:", json.dumps(k["review"]["changes"]))
print("   renamed:", k["review"]["renamed"])
lg2, pub2 = publish(cup, k, league_id=lg["id"], matches=k["review"]["matches"])
out["cup_publish_2"] = {"mode": pub2["mode"], "status": pub2.get("status"), "links": pub2.get("links")}
out["cup_changes"] = k["review"]["changes"]
print("published update:", pub2["mode"], pub2.get("status"))

s = run("shellhacks-smash")
show("smash", s)
lg3, pub3 = publish("ShellHacks Midnight Smash · Demo", s)
out["smash_board"] = f"{BASE}/l/{lg3['id']}"
out["smash_publish"] = {"mode": pub3["mode"], "status": pub3.get("status"), "links": pub3.get("links")}
print("published:", pub3["mode"], pub3.get("status"), pub3.get("links"))

with open("data/demo_shellhacks.json", "w") as f:
    json.dump(out, f, indent=1)
