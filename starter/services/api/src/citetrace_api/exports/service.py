class AnalysisExportService:
    async def export_analysis(self, analysis_id: str, format: str = "json") -> dict[str, str]:
        # Excludes private source text, secret tokens
        if format == "markdown":
            return {"format": "markdown", "content": "# Analysis Export\nProvenance preserved."}
        return {"analysis_id": analysis_id, "status": "exported", "provenance": "preserved"}
