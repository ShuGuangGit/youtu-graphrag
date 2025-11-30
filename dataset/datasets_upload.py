import json
import sys
import os
import time
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.api.core.api_error import ApiError
from tqdm import tqdm
from collections import deque

# --- 引入节流机制 ---
class RateLimiter:
    """
    一个简单的速率限制器，基于时间窗口算法。
    """
    def __init__(self, max_calls, time_window_seconds):
        """
        Args:
            max_calls (int): 在 time_window_seconds 时间内允许的最大调用次数。
            time_window_seconds (float): 时间窗口的长度（秒）。
        """
        self.max_calls = max_calls
        self.time_window_seconds = time_window_seconds
        self.calls = deque()

    def wait_if_needed(self):
        """
        如果当前请求会超过速率限制，则等待直到可以发送请求。
        """
        now = time.time()
        # 移除时间窗口之前的调用记录
        while self.calls and self.calls[0] <= now - self.time_window_seconds:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            # 需要等待，直到最早的那个调用记录过期
            sleep_until = self.calls[0] + self.time_window_seconds
            sleep_time = sleep_until - now
            if sleep_time > 0:
                # print(f"Rate limit approaching, sleeping for {sleep_time:.3f}s...")
                time.sleep(sleep_time)
                # 重新检查队列，因为睡眠期间可能有旧记录过期
                now = time.time()
                while self.calls and self.calls[0] <= now - self.time_window_seconds:
                    self.calls.popleft()

        # 记录当前调用时间
        self.calls.append(now)

# --- 配置 ---
# Langfuse 速率限制假设为每分钟 1000 个请求
# 请根据 Langfuse 官方文档确认实际限制
RATE_LIMIT_PER_MINUTE = 100
RATE_LIMITER = RateLimiter(max_calls=RATE_LIMIT_PER_MINUTE, time_window_seconds=60)

# 429 重试配置
MAX_RETRIES_ON_429 = 5  # 遇到 429 时的最大重试次数
INITIAL_RETRY_DELAY = 1.0  # 初始重试延迟（秒）
BACKOFF_FACTOR = 2.0  # 退避因子 (每次重试延迟时间翻倍)

# 加载环境变量
load_dotenv()

# 获得一个本地的数据集
# 这里采用 https://github.com/hiyouga/LLaMA-Factory/blob/main/data/alpaca_zh_demo.json
alpaca_dataset_path = "dataset/alpaca_zh_demo.json"

# 创建一个用于上传数据集的集合对象
data_to_upload = []

# 读取数据集alpaca_zh_demo.json。注意open的第二个参数模式设置为r,表示Reading
try:
    with open(alpaca_dataset_path, 'r', encoding='utf-8') as alpaca_ds_file:
        data = alpaca_ds_file.read()
        ds_entries = json.loads(data)
        for entry in ds_entries:
            item = {
                "instruction": entry["instruction"],
                "input": entry["input"],
                "expected_output": entry["output"]
            }
            data_to_upload.append(item)
except FileNotFoundError:
    print(f"错误：找不到文件 {alpaca_dataset_path}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"错误：文件 {alpaca_dataset_path} 不是有效的 JSON 格式")
    sys.exit(1)

# 数据集长度
dataset_len = len(data_to_upload)
print(f"已读取 {dataset_len} 条数据。")

# langFuse上的数据集名称,要提前建好
ds_name_in_langfuse = "Alpaca数据集"

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

# 调用tqdm进度条组件来运行时展示进度
for item in tqdm(data_to_upload[:dataset_len], desc="上传数据集项"):
    # 在每次 API 调用前，先检查基本速率限制
    RATE_LIMITER.wait_if_needed()

    success = False
    attempt = 0
    while not success and attempt < MAX_RETRIES_ON_429:
        try:
            langfuse.create_dataset_item(
                dataset_name=ds_name_in_langfuse,
                input=item["instruction"] + item["input"],
                expected_output=item["expected_output"]
            )
            success = True  # 调用成功，跳出重试循环
        except ApiError as e:
            if e.status_code == 429:
                attempt += 1
                if attempt < MAX_RETRIES_ON_429:
                    # 计算本次重试的延迟时间 (指数退避)
                    delay = INITIAL_RETRY_DELAY * (BACKOFF_FACTOR ** (attempt - 1))
                    tqdm.write(f"警告: 429 限流错误，第 {attempt} 次重试，等待 {delay:.2f} 秒...")
                    time.sleep(delay)
                    # 重试前再次检查基本速率限制，因为等待后可能可以发送请求了
                    RATE_LIMITER.wait_if_needed()
                else:
                    # 达到最大重试次数，仍然失败
                    tqdm.write(f"错误: 上传失败 (达到最大重试次数): {item.get('instruction', 'N/A')} - 429 Rate Limit Exceeded after {MAX_RETRIES_ON_429} attempts.")
            else:
                # 遇到其他 API 错误，不重试，直接跳出循环并打印错误
                tqdm.write(f"错误: API Error {e.status_code} - {e.message} for item: {item.get('instruction', 'N/A')}")
                success = True  # 认为这次尝试已经失败，不重试，继续下一个 item
        except Exception as e:
            # 遇到其他非 API 错误，不重试，直接跳出循环并打印错误
            tqdm.write(f"错误: 未知错误 - {e} for item: {item.get('instruction', 'N/A')}")
            success = True  # 认为这次尝试已经失败，不重试，继续下一个 item

print("\n数据集上传完成。")