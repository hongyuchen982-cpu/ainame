<template><view class="page"><view class="hero"><text class="eyebrow">专属知识库</text><text class="title">让 AI 理解你的品牌</text><text class="subtitle">上传 TXT 或 PDF，处理完成后企业命名会优先参考。</text></view><button class="primary upload" :loading="uploading" @click="chooseFile">选择并上传资料</button><text class="section-title">我的资料</text><view v-if="loading" class="loading">正在读取资料…</view><view v-else-if="!files.length" class="empty card"><text class="empty-title">还没有资料</text><text>上传第一份企业资料来建立专属知识库。</text></view><view v-for="item in files" :key="item.id" class="card"><view class="row between"><text class="card-title file-name">{{item.original_name}}</text><text :class="['badge',item.status]">{{statusText[item.status]||item.status}}</text></view><text class="muted">{{size(item.size_bytes)}} · {{date(item.created_at)}} · {{item.chunk_count||0}} 块</text><text v-if="item.error_message" class="error">{{item.error_message}}</text><view class="actions"><button v-if="['failed','completed'].includes(item.status)" class="secondary mini" @click="retry(item)">重新处理</button><button class="danger mini" @click="remove(item)">删除</button></view></view></view></template>
<script setup>
import{ref}from'vue';import{onShow}from'@dcloudio/uni-app';import{api,requireLogin,uploadKnowledge}from'../../api'
const files=ref([]),loading=ref(true),uploading=ref(false),statusText={queued:'排队中',processing:'处理中',completed:'已完成',failed:'失败',deleting:'删除中'}
const size=(n)=>`${((n||0)/1024).toFixed(1)} KB`,date=(v)=>new Date(v).toLocaleString()
async function load(){if(!requireLogin())return;loading.value=true;try{files.value=await api.knowledgeFiles()}catch(e){uni.showToast({title:e.message,icon:'none'})}finally{loading.value=false}}
function chooseFile(){
  // #ifdef H5
  uni.chooseFile({count:1,extension:['.txt','.pdf'],success:({tempFiles})=>upload(tempFiles[0].path)})
  // #endif
  // #ifdef APP-PLUS
  uni.showModal({title:'需要文件选择插件',content:'App 真机选择 PDF/TXT 需要配置原生文件选择插件。当前可先在 H5 上传，App 端仍可查看、重试和删除资料。',showCancel:false})
  // #endif
  // #ifndef H5 || APP-PLUS
  uni.showToast({title:'当前平台请使用 H5 或 App 上传资料',icon:'none'})
  // #endif
}
async function upload(path){uploading.value=true;try{const data=await uploadKnowledge(path);files.value.unshift(data.file);uni.showToast({title:'已进入处理队列',icon:'success'})}catch(e){uni.showToast({title:e.message,icon:'none'})}finally{uploading.value=false}}
async function retry(item){try{const next=await api.reprocessKnowledge(item.id);files.value=files.value.map(v=>v.id===item.id?next:v)}catch(e){uni.showToast({title:e.message,icon:'none'})}}
function remove(item){uni.showModal({title:'确认删除',content:`删除“${item.original_name}”及向量数据？`,success:async({confirm})=>{if(!confirm)return;try{await api.deleteKnowledge(item.id);files.value=files.value.filter(v=>v.id!==item.id)}catch(e){uni.showToast({title:e.message,icon:'none'})}}})}
onShow(load)
</script>
<style scoped>.upload{margin-top:28rpx}.file-name{max-width:65%;word-break:break-all}.card>.muted{display:block;margin-top:14rpx}.error{display:block;color:#a53d35;font-size:22rpx;margin-top:12rpx}.actions{display:flex;gap:12rpx;margin-top:22rpx}.mini{flex:1;min-height:68rpx;font-size:23rpx}</style>
