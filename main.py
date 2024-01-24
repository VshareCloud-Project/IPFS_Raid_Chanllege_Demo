import requests,json,random,base64,time
cid = ""
IPFS_API_URL = "http://127.0.0.1:5010"
IPFS_GATEWAY_URL = "http://127.0.0.1:8080"

#计算CID文件大小
def count_files(cid: str, timeout: int = 120) -> int:
    try:
        ret = requests.post(f"{IPFS_API_URL}/api/v0/object/stat?arg=" + cid, timeout=timeout)
        ret = ret.json()
        return ret["CumulativeSize"]
    except requests.exceptions.Timeout:
        return -1

file_size = count_files(cid)
#获得某个CID的叶子块
def get_leaf_block(cid:str):
    url="http://127.0.0.1:5010/api/v0/ls?arg=%s&headers=true&size=true" % cid
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
    url="http://127.0.0.1:8080/ipfs/%s" % cid
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

#解题挑战
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

#Bench Code
x = 3 #测试次数

n = 1
test_time_list = []
while n <= x:
    print("[Round %s]" % str(n))
    print("生成挑战")
    get_challenge_start_time = time.time()
    challenge = creat_challenge(cid)
    get_challenge_end_time = time.time()
    print("挑战生成完毕，耗时：")
    print(get_challenge_end_time - get_challenge_start_time)
    answer = answer_challenge(challenge)
    answer_time = time.time()
    if answer == challenge['answer']:
        print("挑战验证成功！耗时:")
        print(answer_time - get_challenge_end_time)
        print("计算速度为：")
        print(str(file_size / (answer_time - get_challenge_end_time)) + " Bytes/S")
        test_time_list.append(file_size / (answer_time - get_challenge_end_time))
    else:
        print("挑战验证失败！")
        exit()
    n = n + 1
print("平均计算速度为：")
time_sum = 0
for i in test_time_list:
    time_sum = time_sum +i 
print(str(time_sum/len(test_time_list)) + " Bytes/S")
