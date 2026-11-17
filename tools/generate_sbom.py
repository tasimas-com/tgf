#!/usr/bin/env python3
"""Generate a repository-level SPDX 2.3 JSON SBOM."""
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, sys
from pathlib import Path
from typing import Any

TOOL_VERSION = "1.0.0"

def read_version(root: Path) -> str:
    text = (root / "CMakeLists.txt").read_text(encoding="utf-8")
    match = re.search(r"project\(\s*TGF\s+VERSION\s+([0-9A-Za-z.+-]+)", text, re.I)
    if not match:
        raise ValueError("could not determine TGF project version")
    return match.group(1)

def timestamp(override: str | None = None) -> str:
    value = override if override is not None else os.environ.get("SOURCE_DATE_EPOCH")
    if value is None:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    if str(value).isdigit():
        return dt.datetime.fromtimestamp(int(value), tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be Unix epoch or timezone-aware ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("ISO-8601 creation timestamp must include a timezone")
    return parsed.astimezone(dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")

def spdx_id(repository: str, version: str) -> str:
    repository_part = re.sub(r"[^A-Za-z0-9.-]+","-",repository)
    version_part = re.sub(r"[^A-Za-z0-9.-]+","-",version)
    return f"SPDXRef-{repository_part}-{version_part}"

def build_document(root: Path, manifest: dict[str, Any], created: str | None = None) -> dict[str, Any]:
    version = read_version(root)
    canonical = json.dumps(manifest,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    digest = hashlib.sha256((version+"\n"+canonical).encode("utf-8")).hexdigest()
    packages = [{
        "SPDXID":"SPDXRef-TGF","name":manifest["project"]["name"],"versionInfo":version,
        "downloadLocation":manifest["project"]["repository"],"filesAnalyzed":False,
        "licenseConcluded":manifest["project"]["spdxLicense"],"licenseDeclared":manifest["project"]["spdxLicense"],
        "copyrightText":"NOASSERTION","primaryPackagePurpose":"FRAMEWORK",
        "externalRefs":[{"referenceCategory":"PACKAGE-MANAGER","referenceType":"purl",
                         "referenceLocator":f"pkg:github/tasimas-com/tgf@{version}"}]
    }]
    relationships=[{"spdxElementId":"SPDXRef-DOCUMENT","relationshipType":"DESCRIBES","relatedSpdxElement":"SPDXRef-TGF"}]
    for dep in sorted(manifest["dependencies"],key=lambda x:x["repository"].casefold()):
        packages.append({
            "SPDXID":spdx_id(dep["repository"],dep["version"]),"name":dep["name"],"versionInfo":dep["version"],
            "downloadLocation":dep["sourceUrl"],"filesAnalyzed":False,
            "licenseConcluded":dep["license"],"licenseDeclared":dep["license"],
            "copyrightText":"NOASSERTION","primaryPackagePurpose":"OTHER",
            "sourceInfo":f"scope={dep['scope']}; kind={dep['kind']}; immutable commit={dep['commit']}; not asserted to be linked into TGF runtime binaries.",
            "externalRefs":[{"referenceCategory":"PACKAGE-MANAGER","referenceType":"purl","referenceLocator":dep["purl"]}]
        })
        relationships.append({"spdxElementId":spdx_id(dep["repository"],dep["version"]),
                               "relationshipType":"BUILD_TOOL_OF" if dep["kind"]=="tool" else "DEV_TOOL_OF",
                               "relatedSpdxElement":"SPDXRef-TGF"})
    by_repo={d["repository"]:spdx_id(d["repository"]) for d in manifest["dependencies"]}
    if "mozilla-actions/sccache-action" in by_repo and "mozilla/sccache" in by_repo:
        relationships.append({"spdxElementId":by_repo["mozilla-actions/sccache-action"],
                               "relationshipType":"DEPENDS_ON","relatedSpdxElement":by_repo["mozilla/sccache"]})
    packages.sort(key=lambda x:x["SPDXID"])
    relationships.sort(key=lambda x:(x["spdxElementId"],x["relationshipType"],x["relatedSpdxElement"]))
    return {
        "spdxVersion":"SPDX-2.3","dataLicense":"CC0-1.0","SPDXID":"SPDXRef-DOCUMENT",
        "name":f"TGF-{version}",
        "documentNamespace":f"https://spdx.org/spdxdocs/tgf-{version}-{digest}",
        "creationInfo":{"creators":["Organization: TASIMAS",f"Tool: tgf-sbom-generator-{TOOL_VERSION}"],
                        "created":timestamp(created)},
        "packages":packages,"relationships":relationships,
        "comment":"Direct-component SBOM from third_party/dependencies.json. It lists CI actions and tools but does not recursively expand upstream action bundles, hosted-runner images, OS packages, or compiler/Python distributions."
    }

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,help="Output path; defaults to stdout")
    parser.add_argument("--created",help="Unix epoch or timezone-aware ISO-8601 timestamp")
    args=parser.parse_args()
    root=args.root.resolve()
    try:
        manifest=json.loads((root/"third_party"/"dependencies.json").read_text(encoding="utf-8"))
        output=json.dumps(build_document(root,manifest,args.created),indent=2,sort_keys=True,ensure_ascii=False)+"\n"
        if args.output:
            target=args.output if args.output.is_absolute() else root/args.output
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_suffix(target.suffix+".tmp")
            temporary.write_text(output,encoding="utf-8",newline="\n")
            temporary.replace(target)
            print(f"Wrote SPDX 2.3 SBOM: {target}")
        else:
            sys.stdout.write(output)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(f"SBOM generation failed: {exc}",file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":
    raise SystemExit(main())
