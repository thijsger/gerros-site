/* A purpose-built WebGL watch. No 3D framework, remote models or tracking. */
(() => {
  'use strict';
  const story = document.querySelector('.watch-story');
  if (!story) return;
  const stage = story.querySelector('.watch-stage');
  const visual = story.querySelector('.watch-visual');
  const canvas = document.getElementById('watch-canvas');
  const copies = [...story.querySelectorAll('[data-scene]')];
  const buttons = [...story.querySelectorAll('[data-jump]')];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = document.documentElement.classList.contains('motion-paused');
  let progress = 0, current = -1, manual = null, raf = 0, inView = true;
  const clamp = (n, a=0, b=1) => Math.min(b, Math.max(a,n));
  const mix = (a,b,t) => a+(b-a)*t;
  const smooth = t => t*t*(3-2*t);
  const gl = canvas.getContext('webgl',{alpha:true,antialias:true,powerPreference:'low-power',premultipliedAlpha:false});
  let draw = () => {};
  let failed = !gl;
  const staticMode = () => reduced.matches || failed;
  function select(index){
    if(index===current)return;
    current=index;
    copies.forEach((copy,i)=>{copy.classList.toggle('is-active',i===index);copy.inert=i!==index;copy.setAttribute('aria-hidden',String(i!==index));});
    buttons.forEach((button,i)=>button.setAttribute('aria-pressed',String(i===index)));
    visual.querySelector('img').src=`/assets/web/dials-${['caffi','caffi','racecast','spent'][index]}-454.webp`;
    visual.querySelector('img').alt=`${['Caffi','Caffi','Racecast','Spent'][index]} on a round watch display`;
  }
  function render(){
    raf=0;
    if(!inView)return;
    const bounds=story.getBoundingClientRect();
    if(!staticMode())progress=clamp(-bounds.top/Math.max(1,story.offsetHeight-stage.clientHeight));
    if(manual!==null)progress=manual;
    const index=Math.round(progress*3);
    select(index);
    stage.style.setProperty('--progress',progress);
    draw(progress,index);
  }
  function request(){if(!raf)raf=requestAnimationFrame(render);}
  function mode(){story.classList.toggle('motion-static',staticMode());manual=staticMode()?current<0?0:current/3:null;request();}
  addEventListener('scroll',()=>{if(!staticMode())manual=null;request();},{passive:true});
  addEventListener('resize',request,{passive:true});
  reduced.addEventListener('change',mode);
  new MutationObserver(()=>{paused=document.documentElement.classList.contains('motion-paused');mode();}).observe(document.documentElement,{attributes:true,attributeFilter:['class']});
  new IntersectionObserver(entries=>{inView=entries[0].isIntersecting;if(inView)request();},{rootMargin:'100px'}).observe(story);
  buttons.forEach(button=>button.addEventListener('click',()=>{
    const p=Number(button.dataset.jump)/3;
    if(staticMode()){manual=p;request();}
    else {const top=story.getBoundingClientRect().top+scrollY;window.scrollTo({top:top+p*(story.offsetHeight-stage.clientHeight),behavior:'instant'});request();}
  }));
  if(!gl){mode();request();return;}
  try {
    const vertex=`attribute vec3 position;attribute vec3 normal;attribute vec2 uv;uniform mat4 matrix;uniform mat4 model;varying vec3 n;varying vec3 pos;varying vec2 tex;void main(){vec4 p=model*vec4(position,1.);pos=p.xyz;n=mat3(model)*normal;tex=uv;gl_Position=matrix*p;}`;
    const fragment=`precision mediump float;varying vec3 n;varying vec3 pos;varying vec2 tex;uniform vec3 color;uniform float metal;uniform float screen;uniform sampler2D dial;void main(){vec3 N=normalize(n);vec3 L=normalize(vec3(-3.,4.,6.));vec3 V=normalize(vec3(0.,0.,8.)-pos);float diffuse=max(dot(N,L),0.);float rim=pow(1.-max(dot(N,V),0.),3.);float spec=pow(max(dot(reflect(-L,N),V),0.),mix(20.,95.,metal));vec3 c=color*(.32+diffuse*.82)+vec3(.88,.93,1.)*spec*metal+vec3(.21,.26,.32)*rim*metal;if(screen>.5){c=texture2D(dial,tex).rgb*.96+vec3(.025)*spec;}gl_FragColor=vec4(c,1.);}`;
    function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
    const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('WebGL link failed');gl.useProgram(program);
    const loc={};['matrix','model','color','metal','screen','dial'].forEach(k=>loc[k]=gl.getUniformLocation(program,k));
    const attrs=['position','normal','uv'].map(n=>gl.getAttribLocation(program,n));
    const meshes=[];
    function mesh(vertices,color,metal=0,screen=0){const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);meshes.push({buffer,count:vertices.length/8,color,metal,screen});}
    function tri(out,a,b,c,normal,uvs=[[0,0],[0,0],[0,0]]){[a,b,c].forEach((v,i)=>out.push(...v,...normal,...uvs[i]));}
    function box(cx,cy,cz,x,y,z,color,metal=0){const out=[];const pts=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(p=>[cx+p[0]*x/2,cy+p[1]*y/2,cz+p[2]*z/2]);const faces=[[0,3,2,1,0,0,-1],[4,5,6,7,0,0,1],[0,4,7,3,-1,0,0],[1,2,6,5,1,0,0],[0,1,5,4,0,-1,0],[3,7,6,2,0,1,0]];faces.forEach(f=>{const n=f.slice(4);tri(out,pts[f[0]],pts[f[1]],pts[f[2]],n);tri(out,pts[f[0]],pts[f[2]],pts[f[3]],n);});mesh(out,color,metal);}
    function lathe(profile,color,metal=0,offset=[0,0,0],axis='z',segments=96){const out=[];function transform(p){return axis==='x'?[p[2]+offset[0],p[1]+offset[1],p[0]+offset[2]]:[p[0]+offset[0],p[1]+offset[1],p[2]+offset[2]];}for(let j=0;j<profile.length-1;j++){const [r1,z1]=profile[j],[r2,z2]=profile[j+1];for(let i=0;i<segments;i++){const a=i/segments*Math.PI*2,b=(i+1)/segments*Math.PI*2,m=(a+b)/2;let nr=z2-z1,nz=r1-r2,len=Math.hypot(nr,nz)||1;let n=[Math.cos(m)*nr/len,Math.sin(m)*nr/len,nz/len];if(axis==='x')n=[n[2],n[1],n[0]];const p=[transform([r1*Math.cos(a),r1*Math.sin(a),z1]),transform([r1*Math.cos(b),r1*Math.sin(b),z1]),transform([r2*Math.cos(b),r2*Math.sin(b),z2]),transform([r2*Math.cos(a),r2*Math.sin(a),z2])];tri(out,p[0],p[1],p[2],n);tri(out,p[0],p[2],p[3],n);}}mesh(out,color,metal);}
    // Curved silicone strap, with separate raised ribs and recessed adjustment slots.
    [-1,1].forEach(sign=>{
      for(let i=0;i<13;i++){const y=sign*(1.25+i*.205),z=-.14-Math.pow(i/13,1.7)*.65;box(0,y,z,1.02,.215,.18,[.072,.082,.066]);box(0,y,z+.095,.88,.025,.025,[.115,.125,.096]);if(i>3)box(0,y,z+.105,.16,.065,.015,[.018,.021,.017]);}
      [-1,1].forEach(side=>{box(side*.52,sign*1.18,-.04,.24,.65,.35,[.13,.145,.115],.6);});
    });
    // Back, machined case, sloped metal bezel and glass seat.
    lathe([[0,-.36],[1.18,-.36],[1.36,-.27],[1.42,-.12],[1.42,.1],[1.34,.24],[1.12,.24],[1.1,.16]],[.12,.135,.11],.8);
    lathe([[1.39,.09],[1.405,.13],[1.33,.29],[1.15,.29],[1.1,.23]],[.32,.34,.35],.95);
    lathe([[1.15,.29],[1.12,.315],[1.08,.315],[1.08,.29]],[.045,.05,.04],.4);
    for(let i=0;i<60;i++){const a=i*Math.PI/30;const major=i%5===0;const r=1.245;box(Math.sin(a)*r,Math.cos(a)*r,.293,major?.018:.012,major?.048:.018,.008,major?[.73,.76,.66]:[.36,.39,.31],.3);}
    // Three physical buttons, including a lime accent on the upper start button.
    for(const [side,y,accent] of [[1,.59,true],[1,-.53,false],[-1,.62,false],[-1,0,false],[-1,-.61,false]]){lathe([[.12,side*1.28],[.14,side*1.43],[.11,side*1.49],[0,side*1.49]],accent?[.61,.72,.3]:[.29,.31,.25],.7,[0,y,-.05],'x',24);}
    for(const a of [Math.PI/4,3*Math.PI/4,5*Math.PI/4,7*Math.PI/4]){const x=Math.cos(a)*1.305,y=Math.sin(a)*1.305;lathe([[0,.296],[.047,.296],[.047,.308],[0,.308]],[.065,.075,.058],.8,[x,y,0],'z',16);box(x,y,.31,.053,.009,.005,[.28,.31,.24],.5);}
    const screen=[];for(let i=0;i<120;i++){const a=i*Math.PI/60,b=(i+1)*Math.PI/60;tri(screen,[0,0,.319],[Math.cos(a)*1.075,Math.sin(a)*1.075,.319],[Math.cos(b)*1.075,Math.sin(b)*1.075,.319],[0,0,1],[[.5,.5],[.5+Math.cos(a)*.5,.5-Math.sin(a)*.5],[.5+Math.cos(b)*.5,.5-Math.sin(b)*.5]]);}mesh(screen,[1,1,1],0,1);
    const textures={};
    for(const slug of ['caffi','racecast','spent']){const texture=gl.createTexture();textures[slug]=texture;gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([0,0,0,255]));gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);const img=new Image();img.onload=()=>{gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,img);request();};img.src=`/assets/web/dials-${slug}-454.webp`;}
    function multiply(a,b){const out=new Array(16).fill(0);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)out[c*4+r]+=a[k*4+r]*b[c*4+k];return out;}
    function rotation(x,y,z){const cx=Math.cos(x),sx=Math.sin(x),cy=Math.cos(y),sy=Math.sin(y),cz=Math.cos(z),sz=Math.sin(z);const rx=[1,0,0,0,0,cx,sx,0,0,-sx,cx,0,0,0,0,1],ry=[cy,0,-sy,0,0,1,0,0,sy,0,cy,0,0,0,0,1],rz=[cz,sz,0,0,-sz,cz,0,0,0,0,1,0,0,0,0,1];return multiply(rz,multiply(ry,rx));}
    let width=0,height=0;
    draw=(p,index)=>{
      const ratio=Math.min(devicePixelRatio||1,1.7);const w=Math.round(visual.clientWidth*ratio),h=Math.round(visual.clientHeight*ratio);if(w!==width||h!==height){canvas.width=width=w;canvas.height=height=h;gl.viewport(0,0,w,h);}
      gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);
      const t=p*3,k=Math.min(2,Math.floor(t)),f=smooth(clamp(t-k));
      const poses=[[.28,-.52,-.36,8.4],[-.16,Math.PI*2+.24,.20,7.3],[.24,Math.PI*2-.40,-.24,7.9],[-.12,Math.PI*4+.12,.12,7.5]];
      const pose=poses[k].map((v,i)=>mix(v,poses[k+1][i],f));
      // Reduced motion and paused presentations always show a readable front face.
      if(staticMode() || paused){pose[0]=.1;pose[1]=-.18;pose[2]=-.15;pose[3]=8;}
      const model=rotation(pose[0],pose[1],pose[2]);model[14]=-pose[3];
      const aspect=w/h,near=.1,far=100,focus=1/Math.tan(.65/2);const projection=[focus/aspect,0,0,0,0,focus,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0];
      gl.uniformMatrix4fv(loc.matrix,false,new Float32Array(projection));gl.uniformMatrix4fv(loc.model,false,new Float32Array(model));gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,textures[['caffi','caffi','racecast','spent'][index]]);gl.uniform1i(loc.dial,0);
      for(const m of meshes){gl.bindBuffer(gl.ARRAY_BUFFER,m.buffer);attrs.forEach((a,i)=>{gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,i===2?2:3,gl.FLOAT,false,32,i===0?0:i===1?12:24);});gl.uniform3fv(loc.color,m.color);gl.uniform1f(loc.metal,m.metal);gl.uniform1f(loc.screen,m.screen);gl.drawArrays(gl.TRIANGLES,0,m.count);}
      visual.classList.add('ready');
    };
    canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();visual.classList.remove('ready');failed=true;draw=()=>{};mode();});
    canvas.addEventListener('webglcontextrestored',()=>location.reload());
    mode();request();
  } catch(error){
    visual.classList.remove('ready');failed=true;mode();select(0);request();
    console.warn('3D unavailable; using the original watch screen.',error);
  }
})();
