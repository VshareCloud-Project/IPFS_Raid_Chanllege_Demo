import requests,json,random,base64,time
cid = ""
IPFS_API_URL = "http://127.0.0.1:5010"
IPFS_GATEWAY_URL = "http://127.0.0.1:8080"

#获得某个CID的叶子块
def get_leaf_block(cid:str):
    url=f"{IPFS_API_URL}/api/v0/ls?arg=%s&headers=true&size=true" % cid
    cids = eval(requests.post(url).text)['Objects'][0]['Links']
    return cids
#获得某个CID的所有末端叶子块
def get_extremity_leaf_block_list(cid: str):
    queue = [cid]
    leaf_blocks_list = []

    while queue:
        current_cid = queue.pop(0)
        url = f"{IPFS_API_URL}/api/v0/ls?arg={current_cid}&headers=true&size=true"
        response = requests.post(url)
        links = response.json()['Objects'][0]['Links']

        for link in links:
            if link['Type'] == 2 and int(link['Size']) <= 262144:
                if not get_leaf_block(link['Hash']):  # 如果没有子块，则为叶子块
                    leaf_blocks_list.append(link['Hash'])
            else:
                queue.append(link['Hash'])
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

#生成挑战内容
def creat_challenge(cid:str)->dict:
    challenge = {}
    challenge['cid'] = cid
    challenge_base64_raw = list(devide_raw_base64(get_block_base64(random.choice(get_extremity_leaf_block_list(cid)))))
    challenge['question'] = random.choice(challenge_base64_raw)
    challenge_base64_raw.remove(challenge['question'])
    challenge['answer'] = challenge_base64_raw[0]
    return challenge

cid = ""

start_time = time.time()
challenge = creat_challenge(cid)
# 保存挑战到JSON文件
with open('challenge.json', 'w') as file:
    json.dump(challenge, file)
end_time = time.time()
print("挑战已生成并保存到 'challenge.json'耗时:", end_time - start_time)