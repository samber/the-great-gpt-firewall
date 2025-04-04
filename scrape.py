
import json
import sys
import os
from datetime import datetime
from collections import OrderedDict

import requests

USER_AGENTS = [
    # https://platform.openai.com/docs/bots
    "gptbot",

    # https://platform.openai.com/docs/bots
    "chatgpt-user",

    # https://platform.openai.com/docs/bots
    "oai-searchbot",

    # https://blog.google/technology/ai/an-update-on-web-publisher-controls/
    "google-extended",

    # https://support.apple.com/en-us/119829
    "applebot-extended",

    #
    "anthropic-ai",

    #
    "claudebot",

    #
    "claude-web",

    #
    "amazonbot",

    #
    "cohere-ai",

    # https://docs.perplexity.ai/guides/perplexitybot#perplexitybot
    "perplexitybot",

    # https://commoncrawl.org/ccbot
    "ccbot",

    # https://developers.facebook.com/docs/sharing/bot/
    "facebookbot",

    # https://developers.facebook.com/docs/sharing/webmasters/web-crawlers/
    "meta-externalagent",

    # https://allenai.org/crawler
    "ai2bot",
    "ai2bot-dolma",

    # Diffbot
    "diffbot",

    # https://darkvisitors.com/agents/pangubot
    "pangubot",

    # https://datadome.co/learning-center/how-to-block-petal-bot/
    "petalbot",

    # https://darkvisitors.com/agents/timpibot
    "timpibot",

    # https://about.you.com/fr/youbot/
    "youbot",
]

USER_AGENTS_GP = [
    # The following is commented, because I consider blocking a general purpose crawler is different
    # than blocking a AI model. Detection should be done using the user-agents above.

    # https://webz.io/blog/web-data/what-is-the-omgili-bot-and-why-is-it-crawling-your-website/
    "omgilibot",
    "omgili",
    "webzio-extended",

    "bytespider",
]


year = datetime.now().year
month = datetime.now().strftime('%m')


def load_config():
    with open('_data/websites.json') as file:
        data = json.load(file)
        return data


def scrape_websites(websites):
    index = 0

    def scrape_website(website):
        nonlocal index

        breakdown = {}
        blocked = None

        try:
            url = "https://{}/robots.txt".format(website['domain'])
            headers = {'User-Agent': 'samber/the-great-gpt-firewall/1.0.0'}
            response = requests.get(url, headers=headers, timeout=10)
            body = response.text.lower()

            for ua in USER_AGENTS:
                breakdown[ua] = ua in body
                blocked = blocked or ua in body or False

            for ua in USER_AGENTS_GP:
                # We don't apply blocking here, because I consider a general purpose crawler is different
                # than blocking a AI model. Detection should be done using the user-agents above.
                breakdown[ua] = ua in body

            persistRobotsTxt(website['domain'], body)

        except Exception as e:
            print(e, file=sys.stderr)  # Print the error to stderr
            pass

        index = index + 1
        print("{}/{}: {}".format(index, len(websites),
              website['domain']), file=sys.stderr)

        return {
            "category": website['category'],
            "name": website['name'],
            "domain": website['domain'],
            "country": website['country'],
            "status": None if blocked is None else ("🔐" if blocked else "✅"),
            "breakdown": breakdown,
        }

    return list(map(scrape_website, websites))


def persistRobotsTxt(name, output):
    os.makedirs('{}/{}-{}-robots.txt'.format(year, year, month), exist_ok=True)
    with open('{}/{}-{}-robots.txt/{}.robots.txt'.format(year, year, month, name), 'w') as file:
        file.truncate(0)
        file.write(output)


def persist(output):
    indented_json = json.dumps(output, indent=4, ensure_ascii=False)

    os.makedirs(str(year), exist_ok=True)
    with open('{}/{}-{}.json'.format(year, year, month), 'w') as file:
        file.truncate(0)
        file.write(indented_json)


def generate_markdown(output):
    buffer = ""

    categories = list(OrderedDict.fromkeys(
        (map(lambda x: x['category'], output))).keys())

    for category in categories:
        websites = list(filter(lambda x: x['category'] == category, output))
        # websites = sorted(websites, key=lambda x: x['name'])

        buffer += "### Category: {}\n\n".format(category.capitalize())

        # count per status
        status_count = {}
        total = 0
        for website in websites:
            total += 1
            status_count[website['status']] = status_count.get(
                website['status'], 0) + 1
        buffer += "- Scanned: {}\n- ✅ Passing: {} %\n- 🔐 Blocked: {} %\n- ❓ Unknown: {} %\n\n".format(
            total,
            round(status_count.get("✅", 0) / total * 100),
            round(status_count.get("🔐", 0) / total * 100),
            round(status_count.get(None, 0) / total * 100)
        )

        buffer += "| Name | Country | Status |\n"
        buffer += "| ---- | ------- | ------ |\n"

        for website in websites:
            buffer += "| [{}]({}) | {} | {} |\n".format(
                website['name'],
                "https://" + website['domain'],
                website['country'] or "🌍",
                website['status'] or "❓"
            )

        buffer += "\n"

    print(buffer)

    with open('{}/{}-{}.md'.format(year, year, month), 'w') as file:
        file.truncate(0)
        file.write("## {}-{} update\n\n{}".format(year, month, buffer))


if __name__ == '__main__':
    websites = load_config()
    output = scrape_websites(websites)
    persist(output)
    generate_markdown(output)
