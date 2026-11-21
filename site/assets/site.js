"use strict";
(function(){
  const input=document.querySelector("#search");
  const domain=document.querySelector("#domain");
  const status=document.querySelector("#research-status");
  const grid=document.querySelector("#post-index");
  const count=document.querySelector("#result-count");
  const empty=document.querySelector("#no-results");
  if(!input||!grid||!domain||!status)return;
  const items=Array.from(grid.querySelectorAll(".post-card"));
  function update(){
    const query=input.value.trim().toLocaleLowerCase();
    const cat=domain.value, state=status.value;
    let visible=0;
    for(const item of items){
      const ok=(!query||(item.dataset.search||"").toLocaleLowerCase().includes(query))&&
        (!cat||item.dataset.domain===cat)&&(!state||item.dataset.status===state);
      item.hidden=!ok;if(ok)visible++;
    }
    count.textContent="找到 "+visible+" / "+items.length+" 篇文章";
    empty.hidden=visible!==0;
  }
  for(const target of [input,domain,status])target.addEventListener(target===input?"input":"change",update);
  update();
}());
