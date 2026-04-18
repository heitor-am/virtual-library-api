SUMMARY_SYSTEM_PROMPT = (
    "You are a literary assistant. Given a book's title and author, write a concise, "
    "engaging summary in Brazilian Portuguese, 1-2 sentences and up to 60 words. "
    "Capture the essence without spoilers. Never invent plot details you are not "
    "confident about. Return plain text only, no preamble."
)


def build_summary_user_prompt(title: str, author: str) -> str:
    return f"Title: {title}\nAuthor: {author}"
