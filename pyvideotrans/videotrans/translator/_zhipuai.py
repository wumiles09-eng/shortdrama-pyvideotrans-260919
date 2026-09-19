from dataclasses import dataclass
from videotrans.configure.config import params
from videotrans.translator._openaicompat import OpenAICampat


@dataclass
class ZhipuAI(OpenAICampat):

    def __post_init__(self):
        self.ainame ='zhipuai'
        self.max_tokens =int(params.get('zhipu_max_token',4095))
        self.model_name = params.get('zhipu_model', "glm-5.3-flash")
        # 同一 key 体系有国内站 bigmodel.cn 与国际站 api.z.ai, 充值侧决定可用端点;
        # params.json 设 zhipu_base_url 可切换 (默认国内站, 兼容上游行为)
        self.api_url = params.get('zhipu_base_url', 'https://open.bigmodel.cn/api/paas/v4/')
        self.api_key = params.get('zhipu_key', '')
        self.extra_body={"thinking": {"type": "enabled" if params.get('zhipu_thinking') else "disabled"}}
        super().__post_init__()
