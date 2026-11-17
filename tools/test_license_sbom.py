#!/usr/bin/env python3
"""Regression tests for third-party policy and SPDX generation."""
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import copy, json, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import check_third_party  # noqa: E402
import generate_sbom  # noqa: E402

class LicenseSbomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/"third_party"/"dependencies.json").read_text(encoding="utf-8"))

    def test_repository_policy_passes(self):
        self.assertEqual(check_third_party.check_repository(ROOT),[])

    def test_unapproved_license_is_rejected(self):
        changed=copy.deepcopy(self.manifest)
        changed["dependencies"][0]["license"]="GPL-3.0-only"
        self.assertTrue(any("not approved" in x for x in check_third_party.validate_manifest(changed)))

    def test_manifest_cannot_widen_allowlist(self):
        changed=copy.deepcopy(self.manifest)
        changed["approvedSpdxLicenses"].append("GPL-3.0-only")
        self.assertTrue(any("policy-coded" in x for x in check_third_party.validate_manifest(changed)))

    def test_commit_must_be_full_immutable_sha(self):
        changed=copy.deepcopy(self.manifest)
        changed["dependencies"][0]["commit"]="v7"
        self.assertTrue(any("40-character SHA" in x for x in check_third_party.validate_manifest(changed)))

    def test_cmake_system_modules_are_not_external_dependencies(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/"CMakeLists.txt").write_text(
                "find_package(Threads REQUIRED)\\nfind_package(Python3 3.10 REQUIRED)\\n"
                "find_package(UnregisteredThirdParty REQUIRED)\\n",
                encoding="utf-8"
            )
            errors=check_third_party.validate_cmake(root,self.manifest)
            self.assertEqual(len(errors),1,errors)
            self.assertIn("UnregisteredThirdParty",errors[0])

    def test_spdx_document_and_project_package(self):
        doc=generate_sbom.build_document(ROOT,self.manifest,"2026-11-17T00:00:00Z")
        self.assertEqual(doc["spdxVersion"],"SPDX-2.3")
        self.assertEqual(doc["dataLicense"],"CC0-1.0")
        self.assertEqual(doc["SPDXID"],"SPDXRef-DOCUMENT")
        project=next(x for x in doc["packages"] if x["SPDXID"]=="SPDXRef-TGF")
        self.assertEqual(project["licenseDeclared"],"Apache-2.0")
        self.assertEqual(project["primaryPackagePurpose"],"FRAMEWORK")

    def test_every_dependency_is_in_sbom_with_license_version_and_purl(self):
        doc=generate_sbom.build_document(ROOT,self.manifest,"2026-11-17T00:00:00Z")
        packages={x["name"]:x for x in doc["packages"]}
        self.assertEqual(len(packages),len(self.manifest["dependencies"])+1)
        for dep in self.manifest["dependencies"]:
            package=packages[dep["name"]]
            self.assertEqual(package["versionInfo"],dep["version"])
            self.assertEqual(package["licenseDeclared"],dep["license"])
            self.assertIn(dep["purl"],[x["referenceLocator"] for x in package["externalRefs"]])

    def test_sccache_action_depends_on_pinned_tool(self):
        doc=generate_sbom.build_document(ROOT,self.manifest,"2026-11-17T00:00:00Z")
        rel={(x["spdxElementId"],x["relationshipType"],x["relatedSpdxElement"]) for x in doc["relationships"]}
        action=generate_sbom.spdx_id("mozilla-actions/sccache-action")
        tool=generate_sbom.spdx_id("mozilla/sccache")
        self.assertIn((action,"DEPENDS_ON",tool),rel)

    def test_namespace_is_reproducible_and_registry_sensitive(self):
        first=generate_sbom.build_document(ROOT,self.manifest,"2026-11-17T00:00:00Z")
        self.assertEqual(first,generate_sbom.build_document(ROOT,self.manifest,"2026-11-17T00:00:00Z"))
        changed=copy.deepcopy(self.manifest)
        changed["dependencies"][0]["version"]="v999"
        self.assertNotEqual(first["documentNamespace"],generate_sbom.build_document(ROOT,changed,"2026-11-17T00:00:00Z")["documentNamespace"])

    def test_unregistered_workflow_action_is_rejected(self):
        changed=copy.deepcopy(self.manifest)
        changed["dependencies"]=[x for x in changed["dependencies"] if x["repository"]!="actions/checkout"]
        self.assertTrue(any("not registered" in x for x in check_third_party.validate_workflows(ROOT,changed)))

if __name__=="__main__":
    unittest.main(verbosity=2)
