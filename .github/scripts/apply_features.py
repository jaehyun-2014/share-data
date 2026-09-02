from pathlib import Path
p=Path('materials-center/index.html')
s=p.read_text(encoding='utf-8')
s=s.replace('.report-btn{background:#fff;border:1px solid #f0b7b2;color:#b42318;border-radius:7px;padding:8px 12px}', '.report-btn{background:#fff;border:1px solid #f0b7b2;color:#b42318;border-radius:7px;padding:8px 12px}\n.icon-btn{background:#fff;border:1px solid #d0d5dd;border-radius:7px;width:38px;height:36px;padding:0;font-size:19px;line-height:1;display:inline-flex;align-items:center;justify-content:center}\n.icon-btn:hover{background:#f9fafb}.favorite-btn{color:#475467}.favorite-btn.active{color:#d4a000}.icon-danger{color:#b42318}.icon-edit{color:#344054}.icon-restore{color:#344054}.icon-actions{display:flex;gap:5px;align-items:center;flex-wrap:nowrap}',1)
s=s.replace('<button data-page="library">자료실</button><button data-page="upload">자료 올리기</button>', '<button data-page="library">자료실</button><button data-page="favorites">즐겨찾기</button><button data-page="trash">휴지통</button><button data-page="upload">자료 올리기</button>',1)
s=s.replace('<section id="upload" class="page">','''<section id="favorites" class="page"><div class="card"><h2>즐겨찾기</h2><div id="favoritesBody"></div></div></section>
<section id="trash" class="page"><div class="card"><h2>휴지통</h2><p class="info">삭제한 자료는 휴지통에서 복원하거나 완전히 삭제할 수 있습니다.</p><div class="table-wrap"><table><thead><tr><th>자료 이름</th><th>작성자</th><th>삭제 날짜</th><th>관리</th></tr></thead><tbody id="trashBody"></tbody></table></div></div></section>
<section id="edit" class="page"><div class="card"><h2>자료 수정</h2><input type="hidden" id="editId"><div class="form-row"><label>자료 제목</label><input id="editTitle" placeholder="자료 제목"></div><div class="form-row"><label>작성자(닉네임)</label><input id="editAuthor" placeholder="작성자"></div><div class="form-row"><label>설명</label><textarea id="editDescription" rows="5" placeholder="자료 설명"></textarea></div><button class="primary" onclick="saveMaterialEdit()">저장</button> <button class="secondary" onclick="openPage('library')">취소</button><p id="editMessage" class="message"></p></div></section>

<section id="upload" class="page">''',1)
s=s.replace('let currentUser=null,materials=[],notices=[],profile=null,reports=[];', 'let currentUser=null,materials=[],trashMaterials=[],favorites=[],notices=[],profile=null,reports=[];',1)
s=s.replace('if(id==="library")renderLibrary();\n  if(id==="notice")renderNotices();', 'if(id==="library")renderLibrary();\n  if(id==="favorites")renderFavorites();\n  if(id==="trash")renderTrash();\n  if(id==="notice")renderNotices();',1)
old='''async function loadMaterials(){
  if(!currentUser){materials=[];return}
  const {data,error}=await supabaseClient.from("materials").select("*").order("created_at",{ascending:false});
  if(error){console.error(error);return}
  materials=data||[];
}'''
new='''async function loadMaterials(){
  if(!currentUser){materials=[];trashMaterials=[];favorites=[];return}
  const {data,error}=await supabaseClient.from("materials").select("*").order("created_at",{ascending:false});
  if(error){console.error(error);return}
  const all=data||[];materials=all.filter(m=>!m.deleted_at);trashMaterials=all.filter(m=>m.deleted_at&&m.owner_id===currentUser.id);
  const {data:favData,error:favErr}=await supabaseClient.from("material_favorites").select("material_id").eq("user_id",currentUser.id);
  if(favErr){console.error(favErr);favorites=[]}else favorites=(favData||[]).map(x=>x.material_id);
}'''
assert old in s
s=s.replace(old,new,1)
start=s.index('function materialRow(m){');end=s.index('\nfunction renderHome(){',start)
s=s[:start]+'''function materialRow(m){
  const canOwner=currentUser&&m.owner_id===currentUser.id,isFav=favorites.includes(m.id);
  return `<tr><td><strong>${escapeHtml(m.title)}</strong>${m.description?`<div style="color:#667085;margin-top:5px">${escapeHtml(m.description)}</div>`:""}</td><td>${escapeHtml(displayNameFor(m))}</td><td>${dateText(m.created_at)}</td><td><div class="icon-actions"><button class="icon-btn favorite-btn ${isFav?'active':''}" title="즐겨찾기" aria-label="즐겨찾기" onclick="toggleFavorite('${m.id}')">${isFav?'★':'☆'}</button><button class="icon-btn" title="다운로드" aria-label="다운로드" onclick="downloadMaterial('${m.id}')">↓</button><button class="icon-btn report-btn" title="신고" aria-label="신고" onclick="reportMaterial('${m.id}')">⚑</button>${canOwner?`<button class="icon-btn icon-edit" title="수정" aria-label="수정" onclick="openEdit('${m.id}')">✎</button><button class="icon-btn icon-danger" title="휴지통으로 이동" aria-label="휴지통으로 이동" onclick="deleteMaterial('${m.id}')">×</button>`:""}</div></td></tr>`
}'''+s[end:]
needle='function renderLibrary(){'
ins='''function renderFavorites(){const box=$("favoritesBody");if(!currentUser){box.innerHTML=`<div class="favorite-empty">즐겨찾기를 보려면 로그인해주세요.</div>`;return}const list=materials.filter(m=>favorites.includes(m.id));box.innerHTML=list.length?`<div class="table-wrap"><table><thead><tr><th>자료 이름</th><th>작성자</th><th>업로드 날짜</th><th>관리</th></tr></thead><tbody>${list.map(materialRow).join("")}</tbody></table></div>`:`<div class="favorite-empty">즐겨찾기한 자료가 없습니다.</div>`}
function renderTrash(){const body=$("trashBody");if(!currentUser){body.innerHTML=`<tr><td colspan="4" class="empty">휴지통을 보려면 로그인해주세요.</td></tr>`;return}body.innerHTML=trashMaterials.length?trashMaterials.map(m=>`<tr><td><strong>${escapeHtml(m.title)}</strong></td><td>${escapeHtml(displayNameFor(m))}</td><td>${dateText(m.deleted_at)}</td><td><div class="icon-actions"><button class="icon-btn icon-restore" title="복원" aria-label="복원" onclick="restoreMaterial('${m.id}')">↶</button><button class="icon-btn icon-danger" title="완전 삭제" aria-label="완전 삭제" onclick="permanentDeleteMaterial('${m.id}')">×</button></div></td></tr>`).join(""):`<tr><td colspan="4" class="empty">휴지통이 비어 있습니다.</td></tr>`}

'''
s=s.replace(needle,ins+needle,1)
# add favorite/edit funcs
needle='async function downloadMaterial(id){'
funcs='''async function toggleFavorite(id){if(!currentUser){alert("즐겨찾기를 사용하려면 로그인해주세요.");openPage("auth");return}if(favorites.includes(id)){const {error}=await supabaseClient.from("material_favorites").delete().eq("material_id",id).eq("user_id",currentUser.id);if(error){alert("즐겨찾기 해제 실패: "+error.message);return}favorites=favorites.filter(x=>x!==id)}else{const {error}=await supabaseClient.from("material_favorites").insert({material_id:id,user_id:currentUser.id});if(error&&error.code!=="23505"){alert("즐겨찾기 추가 실패: "+error.message);return}if(!favorites.includes(id))favorites.push(id)}renderHome();renderLibrary();renderFavorites()}
function openEdit(id){if(!currentUser)return;const m=materials.find(x=>x.id===id);if(!m||m.owner_id!==currentUser.id){alert("수정 권한이 없습니다.");return}$("editId").value=m.id;$("editTitle").value=m.title||"";$("editAuthor").value=m.author||"";$("editDescription").value=m.description||"";$("editMessage").textContent="";openPage("edit")}
async function saveMaterialEdit(){if(!currentUser)return;const id=$("editId").value,m=materials.find(x=>x.id===id);if(!m||m.owner_id!==currentUser.id){alert("수정 권한이 없습니다.");return}const title=$("editTitle").value.trim(),author=$("editAuthor").value.trim(),description=$("editDescription").value.trim();if(!title){$("editMessage").textContent="자료 제목을 입력해주세요.";return}const {error}=await supabaseClient.from("materials").update({title,author:author||m.author,description,updated_at:new Date().toISOString()}).eq("id",id).eq("owner_id",currentUser.id);if(error){$("editMessage").textContent="수정 실패: "+error.message;return}$("editMessage").textContent="수정되었습니다.";await loadMaterials();renderHome();renderLibrary();renderFavorites();setTimeout(()=>openPage("library"),400)}

'''
s=s.replace(needle,funcs+needle,1)
# replace delete function
start=s.index('async function deleteMaterial(id){');end=s.index('\nasync function reportMaterial(id){',start)
s=s[:start]+'''async function deleteMaterial(id){if(!currentUser)return;const m=materials.find(x=>x.id===id);if(!m)return;if(m.owner_id!==currentUser.id&&!isAdmin()){alert("삭제 권한이 없습니다.");return}if(!confirm("이 자료를 휴지통으로 이동할까요?"))return;const {error}=await supabaseClient.from("materials").update({deleted_at:new Date().toISOString()}).eq("id",id);if(error){alert("휴지통 이동 실패: "+error.message);return}await loadMaterials();await loadReports();renderHome();renderLibrary();renderFavorites();renderTrash();if(isAdmin())renderAdmin()}
async function restoreMaterial(id){if(!currentUser)return;const m=trashMaterials.find(x=>x.id===id);if(!m||m.owner_id!==currentUser.id){alert("복원 권한이 없습니다.");return}const {error}=await supabaseClient.from("materials").update({deleted_at:null}).eq("id",id).eq("owner_id",currentUser.id);if(error){alert("복원 실패: "+error.message);return}await loadMaterials();renderHome();renderLibrary();renderFavorites();renderTrash()}
async function permanentDeleteMaterial(id){if(!currentUser)return;const m=trashMaterials.find(x=>x.id===id);if(!m||m.owner_id!==currentUser.id){alert("삭제 권한이 없습니다.");return}if(!confirm("이 자료를 완전히 삭제할까요? 되돌릴 수 없습니다."))return;const {error:sErr}=await supabaseClient.storage.from("materials").remove([m.storage_path]);if(sErr){alert("파일 삭제 실패: "+sErr.message);return}const {error:dErr}=await supabaseClient.from("materials").delete().eq("id",id).eq("owner_id",currentUser.id);if(dErr){alert("자료 정보 삭제 실패: "+dErr.message);return}await loadMaterials();renderTrash();renderHome();renderLibrary();renderFavorites()}
'''+s[end:]
s=s.replace('await Promise.all([loadMaterials(),loadNotices(),loadReports()]);renderHome();renderLibrary();renderNotices();if(isAdmin())renderAdmin()', 'await Promise.all([loadMaterials(),loadNotices(),loadReports()]);renderHome();renderLibrary();renderFavorites();renderTrash();renderNotices();if(isAdmin())renderAdmin()',1)
s=s.replace('<button class="download danger" onclick="deleteMaterial(\'${m.id}\')">삭제</button>', '<button class="icon-btn icon-danger" title="휴지통으로 이동" aria-label="휴지통으로 이동" onclick="deleteMaterial(\'${m.id}\')">×</button>',1)
p.write_text(s,encoding='utf-8')