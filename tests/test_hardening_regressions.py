import unittest
from pathlib import Path

from core.upload_validation import (
    resolve_upload_path,
    sanitize_upload_filename,
    validate_upload_metadata,
)
from schemas.name_schemas import NameSchema


class NameSchemaHardeningTest(unittest.TestCase):
    def test_human_and_pet_candidates_do_not_require_domains(self):
        candidate = NameSchema(name="知夏", reference="诗词", moral="明朗温暖")

        self.assertEqual(candidate.domain, "")
        self.assertEqual(candidate.domain_status, "")

    def test_company_candidates_can_include_domain_metadata(self):
        candidate = NameSchema(
            name="星序",
            reference="星辰秩序",
            moral="清晰有序",
            domain="xingxu.com",
            domain_status="可注册",
        )

        self.assertEqual(candidate.domain, "xingxu.com")
        self.assertEqual(candidate.domain_status, "可注册")


class UploadHardeningTest(unittest.TestCase):
    def test_filename_is_reduced_to_a_cross_platform_basename(self):
        self.assertEqual(sanitize_upload_filename(r"..\private\notes.txt"), "notes.txt")
        self.assertEqual(sanitize_upload_filename("../private/report.pdf"), "report.pdf")

    def test_extension_and_mime_type_must_match(self):
        self.assertEqual(
            validate_upload_metadata("report.PDF", "application/pdf; charset=binary"),
            ("report.PDF", ".pdf", "application/pdf"),
        )
        with self.assertRaisesRegex(ValueError, "MIME"):
            validate_upload_metadata("report.pdf", "text/plain")
        with self.assertRaisesRegex(ValueError, "MIME"):
            validate_upload_metadata("report.pdf", "application/octet-stream")
        with self.assertRaisesRegex(ValueError, "仅支持"):
            validate_upload_metadata("payload.exe", "application/octet-stream")

    def test_stored_path_cannot_escape_upload_directory(self):
        upload_dir = Path.cwd() / "__upload_validation_test__"
        self.assertEqual(
            resolve_upload_path(r"C:\legacy\report.pdf", upload_dir),
            (upload_dir / "report.pdf").resolve(),
        )
        with self.assertRaisesRegex(ValueError, "路径不安全"):
            resolve_upload_path("..", upload_dir)


if __name__ == "__main__":
    unittest.main()
