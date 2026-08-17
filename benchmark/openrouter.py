import json
import time
import urllib.error
import urllib.request


class OpenRouterError(RuntimeError):
    pass


def complete(model, system, user, api_key, temperature=0.0):
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": temperature}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "HTTP-Referer": "https://github.com/theletterf/fable-doc-benchmark"}
    started = time.perf_counter()
    for attempt in range(2):
        try:
            request = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(payload).encode(), headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read())
            body["_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
            body["_temperature_sent"] = payload.get("temperature")
            return body
        except urllib.error.HTTPError as exc:
            if exc.code == 400 and "temperature" in payload and attempt == 0:
                payload.pop("temperature")
                continue
            raise OpenRouterError(str(exc)) from exc
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise OpenRouterError(str(exc)) from exc
    raise OpenRouterError("OpenRouter request failed")


def response_text(response):
    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content
