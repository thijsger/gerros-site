'use strict';
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const menu = $('.menu');
menu?.addEventListener('click', () => { const open = menu.getAttribute('aria-expanded') !== 'true'; menu.setAttribute('aria-expanded', String(open)); $('#nav').classList.toggle('open', open); });
document.addEventListener('keydown', e => {if(e.key === 'Escape' && menu?.getAttribute('aria-expanded') === 'true'){menu.click(); menu.focus();}});
$('.theme')?.addEventListener('click', () => {const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; document.documentElement.dataset.theme = dark ? 'light' : 'dark'; $('.theme').setAttribute('aria-label', `Switch to ${dark ? 'dark' : 'light'} mode`);});
$('.motion')?.addEventListener('click', e => {const paused = document.documentElement.classList.toggle('motion-paused'); e.currentTarget.setAttribute('aria-pressed', String(paused)); e.currentTarget.textContent = paused ? 'Play motion' : 'Pause motion';});
$$('[data-rail]').forEach(b => b.addEventListener('click', () => $('.rail').scrollBy({left: Number(b.dataset.rail)*640,behavior: reduce.matches ? 'instant' : 'smooth'})));
if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries => entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('reveal');observer.unobserve(entry.target);}}),{threshold:.12});$$('.section-title,.principles>div:not(.engine-art),.release-list>a,.engine-grid article').forEach(el=>observer.observe(el));}
let category = 'all';
function filter(){const query = $('#app-search').value.trim().toLowerCase();let count = 0;$$('.appgrid .appcard').forEach(a => {a.hidden = !((category === 'all' || a.dataset.cat === category) && a.dataset.search.includes(query));if(!a.hidden) count++;});$('.result-count').textContent = `${count} ${count === 1 ? 'app' : 'apps'} found`;$('.empty').hidden = count !== 0;}
$('#app-search')?.addEventListener('input',filter);
$$('[data-filter]').forEach(b => b.addEventListener('click',()=>{category=b.dataset.filter;$$('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));filter();}));
const modes={predict:['caffi','sobr','jetshift','adapt','racecast','altizone','spent','shiftpay','pitstop','convertr'],guide:['fasted','breathgym','recover','zeitnot','reactr','podium','morsetap'],record:['smokeless','earned','rallypoint','strike','cue','spotsave','listo','remindersplus','cardvault']};
const glance=['caffi','fasted','earned','adapt','racecast','altizone','speedometer-pro','shiftpay','spent','podium','remindersplus','wordclock','redline','triptych'];
let answers=[],step=1;
function showStep(n){step=n;$$('[data-step]').forEach(el=>el.hidden=Number(el.dataset.step)!==n);const title=$(`[data-step="${n}"] h2`);title.setAttribute('tabindex','-1');title.focus({preventScroll:true});}
async function results(){const root=$('.recommendations');root.textContent='Finding your apps…';try{const response=await fetch('/finder-data.json');if(!response.ok)throw Error('Unavailable');const apps=await response.json();const ranked=apps.filter(a=>a.cat===answers[0]).map((a,i)=>({...a,score:(modes[answers[1]]?.includes(a.slug)?4:0)+(glance.includes(a.slug)===(answers[2]==='glance')?2:0)+(a.pending?0:1),i})).sort((a,b)=>b.score-a.score||a.i-b.i).slice(0,3);root.replaceChildren();ranked.forEach(a=>{const link=document.createElement('a');link.className='appcard';link.href=`/apps/${a.slug}/`;const img=document.createElement('img');img.src=`/assets/web/icons-${a.slug}-160.webp`;img.width=85;img.height=85;img.alt='';const copy=document.createElement('span');copy.className='cardcopy';const title=document.createElement('strong');title.textContent=a.name;const tag=document.createElement('span');tag.textContent=a.tag+(a.pending?' · In review':'');copy.append(title,tag);link.append(img,copy);root.append(link);});}catch{root.textContent='The chooser could not load. ';const a=document.createElement('a');a.href='/apps/';a.textContent='Browse the catalogue';root.append(a);}}
$$('[data-answer]').forEach(b=>b.addEventListener('click',()=>{answers[step-1]=b.dataset.answer;if(step===3){showStep(4);results();}else showStep(step+1);}));
$$('.backstep').forEach(b=>b.addEventListener('click',()=>showStep(step-1)));
$('.restart')?.addEventListener('click',()=>{answers=[];showStep(1);});
