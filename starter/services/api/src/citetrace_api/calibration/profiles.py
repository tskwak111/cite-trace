def determine_publish_status(weakest_link: float, balanced_score: float) -> str:
    if weakest_link >= 0.82 and balanced_score >= 0.86:
        return "verified"
    if weakest_link >= 0.55:
        return "limited"
    return "blocked"
