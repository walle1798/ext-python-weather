import asyncio
import logging
from typing import Optional, Dict, Any

import aiohttp
from flask import Flask, request, jsonify

app = Flask(__name__)

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
# 指定群
wx_group_id = "3246531321@chatroom"


async def get(url: str, params: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None, json: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None, retry: int = 3, ssl: bool = True, timeout: float = 10,
    backoff_factor: float = 0.5) -> Any:
    d = await api(url, "GET", params, data, json, headers, retry, ssl, timeout, backoff_factor)
    return d


async def post(url: str, params: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None, json: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None, retry: int = 3, ssl: bool = True, timeout: float = 10,
    backoff_factor: float = 0.5) -> Any:
    d = api(url, "POST", params, data, json, headers, retry, ssl, timeout, backoff_factor)
    return d


async def api(url: str, method: str = "GET", params: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None, json: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None, retry: int = 3, ssl: bool = True, timeout: float = 10,
    backoff_factor: float = 0.5) -> Any:
    timeout = aiohttp.ClientTimeout(total=timeout)
    for attempt in range(retry):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                request_method = getattr(session, method.lower(), session.get)
                async with request_method(url=url, params=params, data=data, json=json, headers=headers,
                                          ssl=ssl) as response:
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        return await response.text()
        except aiohttp.ClientError as e:
            if attempt + 1 == retry:
                raise
            else:
                await asyncio.sleep(backoff_factor * (2 ** attempt))


async def send_text(msg):
    data = {
        "method": "sendText",
        "wxid": wx_group_id,
        "msg": msg,
        "atid": "",
        "pid": 0
    }
    xxx = await api("http://127.0.0.1:8203/api?json&key=86C15C097F05E6FA09D5C7EB0C2CC759EE7C6A4C", method='POST', json=data)
    print(xxx)


# POST 请求示例
@app.route('/', methods=['POST'])
async def echo():
    message = request.json  # 获取 JSON 格式的请求数据
    msg = message.get("msg", "")
    if not msg.endswith("天气"):
        await send_text("正确格式:北京天气")
        return jsonify(content={"message": "Success"}, status_code=200)
    weather_data = await api(f'http://hm.suol.cc/API/tq.php?msg={msg.replace("天气", "")}&n=1')
    print(weather_data)
    weather_lines = weather_data.split("\n")
    weather_info = ""
    additional_info = ""
    for line_number, weather_line in enumerate(weather_lines, 1):
        if "：" in weather_line:
            title, content = weather_line.split("：", 1)
            if title == "预警信息":
                weather_info += content + "\n"
            else:
                weather_info += f"【{title}】 {content}\n"
        else:
            if line_number == 1:
                weather_info += f"【位置】 {weather_line}\n"
            else:
                additional_info = additional_info.rstrip("\n") + "\n" + weather_line if additional_info else weather_line

    if additional_info:
        weather_info += f"【温馨提示】{additional_info}"
    await send_text(weather_info)
    return jsonify(content={"message": "Success"}, status_code=200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=34567)