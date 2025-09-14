def log_lm_execution_cost(lm,activity:str) -> float:
    cost = sum(x["cost"] for x in lm.history if x.get("cost") is not None)
    print(f"{activity} - LLM execution cost:{cost}")
    return cost