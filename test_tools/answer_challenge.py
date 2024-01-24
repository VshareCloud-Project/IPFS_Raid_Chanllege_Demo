import requests,json,base64,time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

IPFS_API_URL = "http://127.0.0.1:5010"
IPFS_GATEWAY_URL = "http://127.0.0.1:8080"

#获得某个CID的叶子块
def get_leaf_block(cid:str):
    url=f"{IPFS_API_URL}/api/v0/ls?arg=%s&headers=true&size=true" % cid
    cids = eval(requests.post(url).text)['Objects'][0]['Links']
    return cids

#获得某个CID的所有末端叶子块 - 多线程
def process_block(cid):
    block_data = get_leaf_block(cid)
    result = []

    for i in block_data:
        if i['Type'] == 1:
            result.append(i['Hash'])
        elif i['Type'] == 2:
            if int(i['Size']) <= 262144:
                if get_leaf_block(i['Hash']) == []:
                    result.append(i['Hash'])
                else:
                    result.extend([leaf['Hash'] for leaf in get_leaf_block(i['Hash'])])
            else:
                result.extend([leaf['Hash'] for leaf in get_leaf_block(i['Hash'])])
    
    return result
#获得某个CID的所有末端叶子块 - 多线程
def get_extremity_leaf_block_list(cid: str, max_workers=10):
    leaf_blocks_list = []
    queue = deque([cid])
    visited = set()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while queue:
            future_to_cid = {executor.submit(process_block, current_cid): current_cid for current_cid in queue}
            queue.clear()
            for future in as_completed(future_to_cid):
                try:
                    result = future.result()
                    for item in result:
                        if item not in visited:
                            queue.append(item)
                            visited.add(item)
                            if get_leaf_block(item) == []:
                                leaf_blocks_list.append(item)
                except Exception as e:
                    print(f"Error processing block: {e}")

    return leaf_blocks_list

#将末端叶子块转化为Base64形式编码
def get_block_base64(cid:str):
    url=f"{IPFS_GATEWAY_URL}/ipfs/%s" % cid
    data = requests.get(url).content
    return str(base64.b64encode(data),encoding='utf-8')

#奇偶分离Base64编码后的数据用以生成挑战问题与答案
def devide_raw_base64(text: str):
    a_base64 = text[::2]  # 获取偶数位置字符
    b_base64 = text[1::2]  # 获取奇数位置字符
    return a_base64, b_base64

def answer_challenge(challenge:dict)->str:
    challenge_cid = challenge['cid']
    leaf_blocks = get_extremity_leaf_block_list(challenge_cid)
    true_answer = ""
    while true_answer == "" :
        for block in leaf_blocks:
            answer_raws = list(devide_raw_base64(get_block_base64(block)))
            for i in answer_raws:
                if i == challenge['question']:
                    answer_raws.remove(challenge['question'])
                    true_answer = answer_raws[0]
                else:
                    pass
    return true_answer

# 从JSON文件读取挑战
with open('challenge.json', 'r') as file:
    challenge = json.load(file)

start_time = time.time()
answer = answer_challenge(challenge)
end_time = time.time()

if answer == challenge['answer']:
    print("挑战验证成功！耗时:", end_time - start_time, "s")
else:
    print("挑战验证失败！")