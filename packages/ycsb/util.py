def get_workload_result(result_str):
    results = result_str.split("\n")
    ret = {}
    skip = True
    for result in results:
        if not result.strip():
            continue
        if not skip:
            if "-" not in result:
                continue
            res = parse_line(result)
            ret[res["key"].lower()] = res["value"]
        if "Run finished" in result:
            skip = False
    return ret


def parse_line(line):
    key = line.split("-")[0].strip()
    values_str = line.split("-")[1].split(",")
    values = {}
    for valueStr in values_str:
        k = valueStr.split(":")[0].strip()
        v = valueStr.split(":")[1].strip()
        values[k] = v
    return {"key": key, "value": values}
