"""
  程序功能：让大模型做题目，并且和标准答案进行比对，比对的结果通过Langchain回调接口给到Langfuse
"""
import uuid
from concurrent.futures import ThreadPoolExecutor
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from llm_app import llm_application
from text_similarity_alg import calc_text_similarity
from dotenv import load_dotenv
import os



# 加载环境变量
load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

#自定义过程：运行llm并评估结果
def run_evaluation(chain, dataset_name, experiment_name):
    #1. 从LangFuse获取指定的数据集
    dataset = langfuse.get_dataset(dataset_name)
    # Initialize the Langfuse handler
    langfuse_handler = CallbackHandler()

    for item in dataset.items:

        # Use the item.run() context manager
        with item.run(
                run_name = experiment_name,
                run_description="My first run",
                run_metadata={"model": "qwen3-max"},
        ) as root_span: # root_span is the root span of the new trace for this item and run.
            # All subsequent langfuse operations within this block are part of this trace.

            # Call your application logic
            output = chain.invoke(item.input, config={"callbacks": [langfuse_handler]})

            # Optionally, score the result against the expected output
            root_span.score_trace(name="exact_match", value = calc_text_similarity(output, item.expected_output))

    print(f"\nFinished processing dataset 'capital_cities' for run '{experiment_name}'.")


#定义在LangFuse上的数据集，比如这里采用测试的数据集"Charles测试数据集"
dataset_name="Alpaca数据集"

#这次实验-数据集测试过程的名称
experiment_name= dataset_name+str(uuid.uuid4())[:8]

#执行评估
run_evaluation(llm_application, dataset_name, experiment_name)