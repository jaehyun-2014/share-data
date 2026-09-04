let currentCommentMaterialId = null;

function commentEscape(v){
  return typeof escapeHtml === 'function' ? escapeHtml(String(v ?? '')) : String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}

async function openComments(id){
  currentCommentMaterialId=id;
  const m=Array.isArray(window.materials)?window.materials.find(x=>x.id===id):(typeof materials!=='undefined'?materials.find(x=>x.id===id):null);
  const modal=document.getElementById('commentModal');
  if(!modal)return;
  document.getElementById('commentTitle').textContent='댓글'+(m?.title?' · '+m.title:'');
  modal.classList.add('open');
  modal.setAttribute('aria-hidden','false');
  document.body.style.overflow='hidden';
  await loadComments(id);
}

function closeComments(){
  const modal=document.getElementById('commentModal');
  if(!modal)return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden','true');
  currentCommentMaterialId=null;
  document.body.style.overflow='';
}

async function getCurrentUser(){
  return (await supabaseClient.auth.getUser()).data.user;
}

function currentNickname(user){
  const name=(document.getElementById('userName')?.textContent||'').trim();
  return name || user?.email?.split('@')[0] || '사용자';
}

async function loadComments(materialId){
  const body=document.getElementById('commentBody');
  const form=document.getElementById('commentForm');
  if(!body||!form)return;
  body.innerHTML='<div class="empty">댓글을 불러오는 중...</div>';
  const {data,error}=await supabaseClient.from('material_comments').select('*').eq('material_id',materialId).is('deleted_at',null).order('created_at',{ascending:true});
  if(error){
    body.innerHTML='<div class="empty">댓글을 불러오지 못했습니다.<br>'+commentEscape(error.message)+'</div>';
    return;
  }
  const user=await getCurrentUser();
  if(!data?.length){
    body.innerHTML='<div class="empty">아직 댓글이 없습니다.</div>';
  }else{
    body.innerHTML=data.map(c=>{
      const mine=!!user&&c.user_id===user.id;
      return '<div class="comment-item"><div class="comment-top"><span class="comment-author">'+commentEscape(c.author_name||'사용자')+'</span><span class="comment-date">'+new Date(c.created_at).toLocaleString('ko-KR')+'</span></div><div class="comment-text">'+commentEscape(c.content)+'</div><div class="comment-actions">'+(mine?'<button type="button" onclick="deleteComment(\''+c.id+'\')">삭제</button>':'')+'<button type="button" class="comment-report" onclick="reportComment(\''+c.id+'\')">신고</button></div></div>';
    }).join('');
  }
  if(user){
    form.innerHTML='<div class="comment-form-row"><textarea id="commentInput" maxlength="1000" placeholder="댓글을 입력하세요."></textarea><button class="primary comment-submit" type="button" onclick="addComment()">등록</button></div><div id="commentMessage" class="message"></div>';
  }else{
    form.innerHTML='<div class="comment-login-note">댓글을 작성하려면 로그인해야 합니다.</div>';
  }
}

async function addComment(){
  if(!currentCommentMaterialId)return;
  const user=await getCurrentUser();
  if(!user){alert('로그인이 필요합니다.');return;}
  const input=document.getElementById('commentInput');
  const content=(input?.value||'').trim();
  if(!content){alert('댓글 내용을 입력하세요.');return;}
  const author_name=currentNickname(user);
  const {error}=await supabaseClient.from('material_comments').insert({material_id:currentCommentMaterialId,user_id:user.id,author_name,content});
  if(error){alert('댓글 등록 실패: '+error.message);return;}
  await loadComments(currentCommentMaterialId);
}

async function deleteComment(id){
  if(!confirm('이 댓글을 삭제할까요?'))return;
  const {error}=await supabaseClient.from('material_comments').update({deleted_at:new Date().toISOString()}).eq('id',id);
  if(error){alert('댓글 삭제 실패: '+error.message);return;}
  if(currentCommentMaterialId)await loadComments(currentCommentMaterialId);
}

async function reportComment(id){
  const user=await getCurrentUser();
  if(!user){alert('로그인이 필요합니다.');return;}
  const reason=prompt('신고 사유를 입력하세요.\n예: 스팸/광고, 욕설/비방, 부적절한 내용');
  if(reason===null)return;
  const text=reason.trim();
  if(!text){alert('신고 사유를 입력하세요.');return;}
  const {error}=await supabaseClient.from('comment_reports').insert({comment_id:id,reporter_id:user.id,reason:text});
  if(error?.code==='23505'){alert('이미 신고한 댓글입니다.');return;}
  if(error){alert('댓글 신고 실패: '+error.message);return;}
  alert('댓글 신고가 접수되었습니다.');
}

async function loadAdminCommentReports(){
  const box=document.getElementById('adminCommentReports');
  if(!box)return;
  const {data,error}=await supabaseClient.from('comment_reports').select('*').order('created_at',{ascending:false});
  if(error){box.innerHTML='<div class="empty">댓글 신고를 불러오지 못했습니다.<br>'+commentEscape(error.message)+'</div>';return;}
  if(!data?.length){box.innerHTML='<div class="empty">댓글 신고 내역이 없습니다.</div>';return;}
  const ids=[...new Set(data.map(x=>x.comment_id))];
  const {data:comments}=await supabaseClient.from('material_comments').select('id,material_id,user_id,author_name,content,deleted_at').in('id',ids);
  const cmap=Object.fromEntries((comments||[]).map(x=>[x.id,x]));
  box.innerHTML=data.map(r=>{
    const c=cmap[r.comment_id];
    return '<div class="admin-comment-report"><strong>'+commentEscape(c?.author_name||'알 수 없음')+'</strong><div class="report-meta">사유: '+commentEscape(r.reason)+'<br>상태: '+commentEscape(r.status)+'<br>신고일: '+new Date(r.created_at).toLocaleString('ko-KR')+'</div><div class="comment-text">'+commentEscape(c?.content||'[삭제된 댓글]')+'</div><div class="admin-comment-actions">'+(r.status==='pending'?'<button type="button" onclick="resolveCommentReport(\''+r.id+'\',\'resolved\')">처리 완료</button><button type="button" onclick="resolveCommentReport(\''+r.id+'\',\'dismissed\')">신고 무시</button>':'')+(c&&!c.deleted_at?'<button type="button" class="danger" onclick="adminDeleteComment(\''+c.id+'\')">댓글 삭제</button>':'')+'</div></div>';
  }).join('');
}

async function resolveCommentReport(id,status){
  const {error}=await supabaseClient.from('comment_reports').update({status}).eq('id',id);
  if(error){alert('처리 실패: '+error.message);return;}
  await loadAdminCommentReports();
}

async function adminDeleteComment(id){
  if(!confirm('이 댓글을 삭제할까요?'))return;
  const {error}=await supabaseClient.from('material_comments').update({deleted_at:new Date().toISOString()}).eq('id',id);
  if(error){alert('댓글 삭제 실패: '+error.message);return;}
  await loadAdminCommentReports();
}

document.addEventListener('DOMContentLoaded',()=>{
  const adminBtn=document.querySelector('[data-page="admin"]');
  if(adminBtn)adminBtn.addEventListener('click',()=>setTimeout(loadAdminCommentReports,100));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeComments();});
});
