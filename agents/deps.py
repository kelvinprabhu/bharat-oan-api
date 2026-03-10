from typing import Optional
from pydantic import BaseModel, Field
from app.config import settings


# Zambia-specific language display names.
# The `langcodes` library does not recognise 'bem' or 'nya' as standard BCP-47
# codes, so we maintain a manual mapping here.
ZAMBIA_LANG_DISPLAY: dict[str, str] = {
    "en":  "English",
    "bem": "Cibemba",
    "nya": "Chinyanja",
}


class FarmerContext(BaseModel):
    """Context for the farmer agent.
    
    Args:
        query (str): The user's question.
        lang_code (str): The language code of the user's question.
            Supported values: 'en' (English), 'bem' (Cibemba), 'nya' (Chinyanja).
        session_id (str): The session ID for the conversation.
        moderation_str (Optional[str]): The moderation result of the user's question.


    Example:
        **User:** "Chimaize chili pa mtengo wochuluka bwanji ku Kabwe?"
        **Selected Language:** Chinyanja
        **Moderation Compliance:** "Valid Agricultural (This is a valid agricultural question.)"
    """
    query: str = Field(description="The user's question.")
    lang_code: str = Field(
        description="The language code of the user's question. Supported: 'en', 'bem', 'nya'.",
        default=settings.default_language
    )
    session_id: str = Field(description="The session ID for the conversation.")
    moderation_str: Optional[str] = Field(default=None, description="The moderation result of the user's question.")

    def update_moderation_str(self, moderation_str: str):
        """Update the moderation result of the user's question."""
        self.moderation_str = moderation_str

    def _language_string(self):
        """Get the language string for the agrinet agent.

        Uses a Zambia-specific mapping for 'bem' and 'nya' since these codes
        are not recognised by the langcodes BCP-47 library.
        """
        display = ZAMBIA_LANG_DISPLAY.get(self.lang_code, "English")
        return f"**Selected Language:** {display}"
    
    def _query_string(self):
        """Get the query string for the agrinet agent."""
        return "**User:** " + '"' + self.query + '"'

    def _moderation_string(self):
        """Get the moderation string for the agrinet agent."""
        if self.moderation_str:
            return self.moderation_str
        else:
            return None
    
    def get_user_message(self):
        """Get the user message for the agrinet agent."""
        strings = [self._query_string(), self._language_string(), self._moderation_string()]
        return "\n".join([x for x in strings if x])