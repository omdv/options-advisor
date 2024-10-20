"""
Routines to get market quotes
"""
import requests


def api_assistant(config):
    """
    Get assistant information for given prompt
    """
    api_key = config['assistant_api_key']
    prompt = config['assistant_prompt']

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": config['assistant_model'],
        "messages": [{
            "role": "system",
            "content": "You are a helpful assistant. " +
                "Be concise and precise. " +
                "Provide references. "
        },
        {
            "role": "user",
            "content": prompt
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from API: {e}")
        return None

    try:
        result = response.json()
        message = result["choices"][0]["message"]["content"]
        return message
    except ValueError:
        print(f"Failed to parse data from API: {response.json()}")
        return "Failed to parse"
