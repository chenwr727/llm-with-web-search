ANALYZE_SEARCH_PROMPT = """作为AI助手，请基于用户发送的消息，判断是否需要联网搜索并提取关键词。

# 用户消息为：
{question}

请以JSON格式返回，包含以下字段：
1. needs_search: 布尔值，表示是否需要搜索。如果问题可以通过已有知识回答，则为 false；否则为 true。
2. search_queries: 字符串列表，包含1-3个搜索关键词组合。每个关键词组合应简洁精确，并按重要性排序。
3. reason: 字符串，说明为什么需要或不需要搜索。

**注意- 今天是{cur_date}。**

输出字段示例：
```json
{{
    "needs_search": true,
    "search_queries": ["2025 AI 技术趋势", "最新人工智能发展 2025", "AI 创新应用 2025"],
    "reason": "问题涉及2025年的最新信息，需要搜索确认"
}}
```

搜索关键词要求：
1. 每个关键词组合应该用不同的表达方式，以提高搜索效果。
2. 关键词应该简洁精确，去除无关词语。
3. 如涉及时效性信息，需包含年份或时间范围。
4. 按重要性排序，最重要的搜索词组合放在首位。

判断是否需要搜索的标准：
1. 如果问题涉及时效性信息（如最新新闻、近期事件），则需要搜索。
2. 如果问题需要具体事实或数据支持（如统计数据、专业术语解释），则需要搜索。
3. 如果问题可以通过常识或已有知识回答，则不需要搜索。

异常处理规则：
1. 如果对话历史为空，仅根据当前问题进行判断。
2. 如果当前问题模糊不清（如“随便聊聊”），返回 needs_search 为 false，并在 reason 中说明原因。
3. 如果无法提取有效的搜索关键词，返回空列表 []，并在 reason 中说明原因。

请仅返回JSON格式数据。"""

FILTER_RESULTS_PROMPT = """请分析以下搜索结果，提取与查询"{query}"最相关的核心内容。

要求：
1. 保留与查询词"{query}"直接相关的信息。
2. 删除无关内容（如广告、推广信息等）。
3. 总字数尽量控制在200字以内；如果内容复杂，可扩展至300字，但需保持语言简洁清晰。
4. 提取的核心内容应以自然段落形式呈现；如果有多个相关信息点，可以用分号或编号分隔。

相关性判断标准：
1. 内容必须直接提及查询词中的核心关键词。
2. 如果内容涉及查询词的背景、发展趋势或具体案例，则视为相关。
3. 广告、推广信息或与查询词无直接关联的内容视为无关。

异常处理规则：
1. 如果搜索结果完全无关，返回"未找到与查询相关的内容"。
2. 如果搜索结果过短（少于50字），直接返回原文。
3. 如果搜索结果过长，优先提取最相关的核心部分。

搜索结果：
{content}

请直接返回提取后的内容，无需其他解释。"""

GENERATE_ANSWER_WITH_SEARCH_PROMPT = """# 以下内容是基于用户发送的消息的搜索结果:
{search_results}
在我给你的搜索结果中，每个结果都是[webpage X begin]{{"title":"...", "content": "...", "source": ""https://XXX""}}[webpage X end]格式的，X代表每篇文章的数字索引。请在适当的情况下在句子末尾引用上下文。请按照引用编号<sup><a href=source target="_blank">X</a></sup>的格式在答案中对应部分引用上下文。如果一句话源自多个上下文，请列出所有相关的引用编号，例如<sup><a href=source target="_blank">3</a></sup> <sup><a href=source target="_blank">5</a></sup>，多个引用编号之间用空格分隔，切记不要将引用集中在最后返回引用编号，而是在答案对应部分列出。
在回答时，请注意以下几点：
- 今天是{cur_date}。
- 并非搜索结果的所有内容都与用户的问题密切相关，你需要结合问题，对搜索结果进行甄别、筛选。
- 对于列举类的问题（如列举所有航班信息），尽量将答案控制在10个要点以内，并告诉用户可以查看搜索来源、获得完整信息。优先提供信息完整、最相关的列举项；如非必要，不要主动告诉用户搜索结果未提供的内容。
- 对于创作类的问题（如写论文），请务必在正文的段落中引用对应的参考编号，例如<sup><a href=source target="_blank">3</a></sup> <sup><a href=source target="_blank">5</a></sup>，不能只在文章末尾引用。你需要解读并概括用户的题目要求，选择合适的格式，充分利用搜索结果并抽取重要信息，生成符合用户要求、极具思想深度、富有创造力与专业性的答案。你的创作篇幅需要尽可能延长，对于每一个要点的论述要推测用户的意图，给出尽可能多角度的回答要点，且务必信息量大、论述详尽。
- 如果回答很长，请尽量结构化、分段落总结。如果需要分点作答，尽量控制在5个点以内，并合并相关的内容。
- 对于客观类的问答，如果问题的答案非常简短，可以适当补充一到两句相关信息，以丰富内容。
- 你需要根据用户要求和回答内容选择合适、美观的回答格式，确保可读性强。
- 你的回答应该综合多个相关网页来回答，不能重复引用一个网页。
- 除非用户要求，否则你回答的语言需要和用户提问的语言保持一致。

# 用户消息为：
{question}"""

GENERATE_ANSWER_PROMPT = """作为AI助手，请基于用户发送的消息回答：

# 用户消息为：
{question}"""
