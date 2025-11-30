"""
  程序功能：LLM应用，它由三部分组成：基于提示词模板构建的提示词+LLM模型+输出解析器
"""
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

load_dotenv()

llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
llm_base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
llm_api_key = os.getenv("LLM_API_KEY", "")


#基于提示词模板构建提示词
prompt=PromptTemplate.from_template("""
*********
你是一位Mr Know All先生，世界万物的知识你无所不知。
问个问题:{input}
*********""")
#待测试的模型

llm = ChatOpenAI(
    api_key=llm_api_key,
    base_url=llm_base_url,
    model=llm_model,
    temperature=0
)

#给出输出解析器，这里是StrOutputParser，它会把AIMessage转为str
parser = StrOutputParser()
#创建一个langchain链，它会提示词+模型+解析器  结合起来
llm_application = (
        prompt
        | llm
        | parser
)
