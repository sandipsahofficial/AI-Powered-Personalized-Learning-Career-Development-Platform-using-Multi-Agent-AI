import re
import io
import zipfile
import logging
import xml.etree.ElementTree as ET
from typing import Tuple, List, Dict
from pypdf import PdfReader
from fastapi import HTTPException, status, UploadFile
from app.schemas.profiling import DocumentSection, DocumentUploadResponse

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/octet-stream"
}

# Regex for common resume section headers
SECTION_PATTERNS = {
    "Technical Skills": r"(?:technical\s+skills|skills|technologies|core\s+competencies|tools\s*(?:&|and)\s*technologies)",
    "Experience": r"(?:work\s+experience|professional\s+experience|experience|employment\s+history|internships)",
    "Projects": r"(?:personal\s+projects|academic\s+projects|key\s+projects|projects)",
    "Education": r"(?:academic\s+background|education|qualifications|academic\s+credentials)",
    "Certifications": r"(?:certifications|licenses\s*(?:&|and)\s*certifications|professional\s+certifications)",
    "Achievements": r"(?:achievements|honors\s*(?:&|and)\s*awards|accomplishments)"
}

# Prompt injection patterns to sanitize
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"ignore\s+above\s+and",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"system\s*prompt\s*:",
    r"give\s+this\s+candidate\s+(?:an?\s+)?expert",
    r"rate\s+all\s+skills\s+as\s+5",
    r"override\s+evaluation",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
]


class DocumentParser:
    @staticmethod
    def validate_file(filename: str, content: bytes, content_type: str = "") -> str:
        """
        Validates file extension and size. Returns lower-case extension.
        """
        if not filename or "." not in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. A valid file with extension (.pdf, .docx, .txt) is required."
            )

        ext = "." + filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
            )

        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        return ext

    @classmethod
    def extract_text_from_pdf(cls, content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            extracted_pages = []
            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(text)
            
            full_text = "\n\n".join(extracted_pages).strip()
            if not full_text:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No extractable text found in PDF. The document may be scanned or image-only."
                )
            return full_text
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to parse PDF document: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Corrupted or invalid PDF file: {str(e)}"
            )

    @classmethod
    def extract_text_from_docx(cls, content: bytes) -> str:
        try:
            # DOCX is an open XML zip package containing word/document.xml
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                if "word/document.xml" not in z.namelist():
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Invalid DOCX structure: missing word/document.xml"
                    )
                xml_data = z.read("word/document.xml")
            
            root = ET.fromstring(xml_data)
            # Namespace for WordprocessingML
            namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            
            paragraphs = []
            for p in root.findall(".//w:p", namespaces):
                texts = [node.text for node in p.findall(".//w:t", namespaces) if node.text]
                if texts:
                    paragraphs.append("".join(texts))

            full_text = "\n".join(paragraphs).strip()
            if not full_text:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No extractable text found in DOCX file."
                )
            return full_text
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to parse DOCX document: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Corrupted or invalid DOCX file: {str(e)}"
            )

    @classmethod
    def extract_text_from_txt(cls, content: bytes) -> str:
        try:
            text = content.decode("utf-8").strip()
            if not text:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Text file is empty."
                )
            return text
        except UnicodeDecodeError:
            try:
                return content.decode("latin-1").strip()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unable to decode text file encoding: {str(e)}"
                )

    @classmethod
    def sanitize_and_clean_text(cls, raw_text: str) -> str:
        """
        Removes null bytes, excessive whitespace, and neutralizes prompt injection attempts.
        """
        # Remove null bytes
        cleaned = raw_text.replace("\x00", "")
        
        # Neutralize known prompt injection attempts
        for pattern in INJECTION_PATTERNS:
            cleaned = re.sub(pattern, "[SANITIZED_INPUT]", cleaned, flags=re.IGNORECASE)

        # Normalize unicode hyphens & quotes
        cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'").replace("–", "-")
        
        # Condense whitespace
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @classmethod
    def segment_sections(cls, cleaned_text: str) -> List[DocumentSection]:
        """
        Segments text into canonical sections using line-based regex headers.
        """
        lines = cleaned_text.split("\n")
        sections: List[DocumentSection] = []
        current_title = "General Information"
        current_lines: List[str] = []

        for line in lines:
            line_stripped = line.strip()
            matched_section = None

            # Check if line acts as a header (typically short, <= 45 chars)
            if 2 <= len(line_stripped) <= 45:
                for section_name, pattern in SECTION_PATTERNS.items():
                    if re.match(r"^[\s#*_-]*" + pattern + r"[\s:*-]*$", line_stripped, re.IGNORECASE):
                        matched_section = section_name
                        break

            if matched_section:
                # Save previous section if it has content
                content_str = "\n".join(current_lines).strip()
                if content_str:
                    sections.append(DocumentSection(
                        title=current_title,
                        content=content_str,
                        char_count=len(content_str)
                    ))
                current_title = matched_section
                current_lines = []
            else:
                current_lines.append(line)

        # Append last section
        final_content = "\n".join(current_lines).strip()
        if final_content:
            sections.append(DocumentSection(
                title=current_title,
                content=final_content,
                char_count=len(final_content)
            ))

        return sections

    @classmethod
    def parse_document(cls, filename: str, content: bytes, content_type: str = "") -> DocumentUploadResponse:
        ext = cls.validate_file(filename, content, content_type)

        if ext == ".pdf":
            raw_text = cls.extract_text_from_pdf(content)
        elif ext == ".docx":
            raw_text = cls.extract_text_from_docx(content)
        elif ext == ".txt":
            raw_text = cls.extract_text_from_txt(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        cleaned_text = cls.sanitize_and_clean_text(raw_text)
        sections = cls.segment_sections(cleaned_text)
        detected_names = [s.title for s in sections if s.title != "General Information"]

        preview_len = min(600, len(cleaned_text))
        preview = cleaned_text[:preview_len] + ("..." if len(cleaned_text) > preview_len else "")

        return DocumentUploadResponse(
            filename=filename,
            file_type=ext[1:].upper(),
            size_bytes=len(content),
            char_count=len(cleaned_text),
            sections_detected=detected_names,
            sections=sections,
            extracted_text_preview=preview
        )
