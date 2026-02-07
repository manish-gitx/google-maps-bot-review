import random
from openai import OpenAI
from utils.logger import log
import config


def generate_review(place_name: str = "this place", rating: int = 5) -> str:
    """Generate a unique, human-sounding review using OpenAI.

    Falls back to template-based generation if OpenAI is unavailable.
    """
    if config.OPENAI_API_KEY:
        try:
            return _generate_with_openai(place_name, rating)
        except Exception as e:
            log.warning(f"OpenAI review generation failed, using fallback: {e}")

    return _generate_fallback(rating)


def _generate_with_openai(place_name: str, rating: int) -> str:
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    sentiment = "very positive" if rating >= 4 else "mixed" if rating == 3 else "negative"
    star_text = f"{rating} out of 5 stars"

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": """You write short, casual Google Maps reviews that sound like real people.

Rules:
- 1-3 sentences maximum. Most Google reviews are short.
- Sound like a normal person, NOT a professional writer
- Use casual language, minor grammar imperfections are OK
- Be specific but not overly detailed
- NO emojis unless you'd naturally use one
- NO hashtags, NO "highly recommend" cliches
- Vary your style: sometimes start with "Great", sometimes describe what you did
- Occasionally include a minor complaint even in positive reviews (realistic)
- DO NOT mention being an AI or that this is generated
- Just output the review text, nothing else""",
            },
            {
                "role": "user",
                "content": f"Write a {sentiment} Google Maps review ({star_text}) for: {place_name}",
            },
        ],
        max_tokens=150,
        temperature=1.1,
    )

    review = response.choices[0].message.content.strip()
    if review.startswith('"') and review.endswith('"'):
        review = review[1:-1]

    log.info(f"OpenAI generated review: {review[:60]}...")
    return review


def generate_batch_reviews(place_name: str, count: int = 5, rating_range: tuple = (4, 5)) -> list[dict]:
    """Generate multiple unique reviews at once via OpenAI."""
    if not config.OPENAI_API_KEY:
        return [
            {"text": _generate_fallback(random.randint(*rating_range)),
             "rating": random.randint(*rating_range)}
            for _ in range(count)
        ]

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You generate multiple distinct Google Maps reviews.

Each review should:
- Be 1-3 sentences, casual tone
- Sound like a DIFFERENT person wrote each one
- Vary vocabulary, sentence structure, and personality
- Some should be enthusiastic, some more reserved/matter-of-fact
- Mix in minor typos or grammar quirks occasionally (realistic)
- NO emojis unless natural, NO "highly recommend" cliches

Output format (one review per line, prefixed with star rating):
5|Great food and nice atmosphere. We sat outside and really enjoyed it.
4|Solid place, nothing to complain about really. Service was quick.
5|loved it here!! the staff were so friendly and the portions were huge""",
                },
                {
                    "role": "user",
                    "content": f"Generate {count} unique Google Maps reviews for: {place_name}\n"
                               f"Star ratings should range from {rating_range[0]} to {rating_range[1]}.",
                },
            ],
            max_tokens=count * 100,
            temperature=1.1,
        )

        raw = response.choices[0].message.content.strip()
        reviews = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                parts = line.split("|", 1)
                try:
                    r = int(parts[0].strip())
                    text = parts[1].strip().strip('"')
                    reviews.append({"text": text, "rating": r})
                except (ValueError, IndexError):
                    reviews.append({"text": line, "rating": random.randint(*rating_range)})
            else:
                reviews.append({"text": line, "rating": random.randint(*rating_range)})

        log.info(f"Generated {len(reviews)} reviews via OpenAI")
        return reviews[:count]

    except Exception as e:
        log.warning(f"Batch generation failed: {e}")
        return [
            {"text": _generate_fallback(random.randint(*rating_range)),
             "rating": random.randint(*rating_range)}
            for _ in range(count)
        ]


# ------------------------------------------------------------------ #
#                     Fallback Template Generator                      #
# ------------------------------------------------------------------ #

_TEMPLATES = [
    "Had a {adj} experience here. The {aspect} was {quality} and I {action}. {close}",
    "Really {adj} place. {aspect} {quality}. {close}",
    "{greet} {aspect} was {quality}. {action}. {close}",
    "Came here {when} and {action}. The {aspect} is {quality}. {close}",
    "{action}. {aspect} was {quality} and the {aspect2} was great too. {close}",
]

_POOL = {
    "adj": ["great", "wonderful", "fantastic", "nice", "lovely", "amazing", "excellent", "solid"],
    "aspect": ["service", "food", "atmosphere", "staff", "vibe", "location", "ambiance",
                "quality", "selection", "decor", "pricing", "cleanliness"],
    "quality": ["really good", "top notch", "impressive", "excellent", "better than expected",
                "outstanding", "quite nice", "on point", "superb"],
    "action": ["would definitely come back", "really enjoyed my time", "had a great time",
               "left feeling satisfied", "was pleasantly surprised", "loved it overall"],
    "greet": ["Visited last week and", "Stopped by recently and", "Went here for the first time and",
              "Finally tried this place and", "Checked this out on a whim and"],
    "close": ["Would recommend!", "Definitely coming back.", "Worth a visit.", "Give it a try!",
              "Solid choice.", "Happy I found this place.", "", ""],
    "when": ["last week", "a few days ago", "over the weekend", "recently", "yesterday",
             "for lunch", "with some friends"],
}


def _generate_fallback(rating: int = 5) -> str:
    tmpl = random.choice(_TEMPLATES)
    aspects = random.sample(_POOL["aspect"], 2)
    review = tmpl.format(
        adj=random.choice(_POOL["adj"]),
        aspect=aspects[0], aspect2=aspects[1],
        quality=random.choice(_POOL["quality"]),
        action=random.choice(_POOL["action"]),
        greet=random.choice(_POOL["greet"]),
        close=random.choice(_POOL["close"]),
        when=random.choice(_POOL["when"]),
    )
    return review.strip()
