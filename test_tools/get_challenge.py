import requests,json,random,base64,time

IPFS_API_URL = "http://127.0.0.1:5010"
IPFS_GATEWAY_URL = "http://127.0.0.1:8080"
DRAND_URL = "https://drand.cloudflare.com/8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce/public/latest"

#获得某个CID的叶子块
def get_leaf_block(cid:str):
    url=f"{IPFS_API_URL}/api/v0/ls?arg=%s&headers=true&size=true" % cid
    cids = eval(requests.post(url).text)['Objects'][0]['Links']
    return cids

#从drand获得最新的随机数
def get_random_number():
    url = f"{DRAND_URL}"
    response = requests.get(url)
    data = response.json()
    return int(data["randomness"], 16)

#获得随机的n个末端叶子块
def get_random_leaf_block_list(cid: str, max_leaf_blocks: int):
    if get_leaf_block(cid) == []:
        return [cid]

    top_leaf_blocks_list = get_leaf_block(cid)
    leaf_blocks_list = []

    while top_leaf_blocks_list and len(leaf_blocks_list) < max_leaf_blocks:
        current_block = random.choice(top_leaf_blocks_list)
        top_leaf_blocks_list.remove(current_block)

        while current_block['Type'] != 2 or int(current_block['Size']) > 262144 or get_leaf_block(current_block['Hash']) != []:
            child_blocks = get_leaf_block(current_block['Hash'])
            if not child_blocks:  # 如果没有更多的子块，跳出内部循环
                break
            current_block = random.choice(child_blocks)

        leaf_blocks_list.append(current_block['Hash'])
    print(leaf_blocks_list)
    return leaf_blocks_list

#选取一个末端叶子块
def select_leaf_blocks_by_drand(leaf_blocks_list):
    leaf_blocks_list.sort()  # 按字母顺序排序
    round_number = get_random_number()
    selected_index = round_number % len(leaf_blocks_list)
    print(f"随机数：{round_number}, 选中的叶子块：{leaf_blocks_list[selected_index]}")
    return leaf_blocks_list[selected_index]

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

#生成挑战内容
def creat_challenge(cid: str,max_leaf_blocks: int)->dict:
    challenge = {}
    challenge['cid'] = cid
    challenge_base64_raw = list(devide_raw_base64(get_block_base64(select_leaf_blocks_by_drand(get_random_leaf_block_list(cid, max_leaf_blocks)))))
    challenge['question'] = random.choice(challenge_base64_raw)
    challenge_base64_raw.remove(challenge['question'])
    challenge['answer'] = challenge_base64_raw[0]
    return challenge

cid = ""
max_leaf_blocks = 5 #最大叶子块数量

start_time = time.time()
challenge = creat_challenge(cid,max_leaf_blocks)
# 保存挑战到JSON文件
with open('challenge.json', 'w') as file:
    json.dump(challenge, file)
end_time = time.time()
print("挑战已生成并保存到 'challenge.json'耗时:", end_time - start_time, "s")