/**
 * Snapmaker U1 3D Viewer (Three.js)
 * Gestisce il rendering WebGL, l'illuminazione, il piatto PEI e i materiali.
 */
class ModelViewer {
  constructor(canvasContainerId) {
    this.container = document.getElementById(canvasContainerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.modelGroup = new THREE.Group();
    this.partMeshes = [];
    this.wireframeMode = false;

    this.init();
  }

  init() {
    // 1. Scena
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0e1014);

    // 2. Camera
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(40, width / height, 0.5, 2000);
    this.camera.position.set(0, -110, 95);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
      preserveDrawingBuffer: true,
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Spazio colore sRGB calibrato per fedeltÃ  cromatica esatta
    if (typeof THREE.ColorManagement !== "undefined" && THREE.ColorManagement.enabled !== undefined) {
      THREE.ColorManagement.enabled = true;
    }
    if ("outputColorSpace" in this.renderer && typeof THREE.SRGBColorSpace !== "undefined") {
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    } else if ("outputEncoding" in this.renderer && typeof THREE.sRGBEncoding !== "undefined") {
      this.renderer.outputEncoding = THREE.sRGBEncoding;
    }

    if (typeof THREE.NoToneMapping !== "undefined") {
      this.renderer.toneMapping = THREE.NoToneMapping;
    }

    this.renderer.domElement.style.touchAction = "none";
    this.container.appendChild(this.renderer.domElement);

    // 4. OrbitControls Touch-friendly con rotazione libera 360°
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minPolarAngle = 0;
    this.controls.maxPolarAngle = Math.PI * 0.95; // Rotazione completa a 360° evitando glitch al nadir
    this.controls.minAzimuthAngle = -Infinity;
    this.controls.maxAzimuthAngle = Infinity;
    this.controls.minDistance = 15;
    this.controls.maxDistance = 500;
    this.controls.target.set(0, 0, 2);
    if (THREE.TOUCH) {
      this.controls.touches = {
        ONE: THREE.TOUCH.ROTATE,
        TWO: THREE.TOUCH.DOLLY_PAN
      };
    }

    // 5. Setup Luci
    this.setupLighting();

    // 6. Piatto Snapmaker U1 (270x270 mm PEI testurizzato)
    this.setupBuildPlate();

    // 7. Aggiungi gruppo modello
    this.scene.add(this.modelGroup);

    // 8. Eventi Resize
    window.addEventListener("resize", () => this.onWindowResize());

    // 9. Loop di Render
    this.animate();
  }

  setupLighting() {
    // Luce d'ambiente neutra bilanciata (evita sovraesposizione che sbianca i colori)
    const ambient = new THREE.AmbientLight(0xffffff, 0.42);
    this.scene.add(ambient);

    // Luce primaria superiore frontale neutra (esalta il rilievo senza bruciare le alte luci)
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.68);
    dirLight1.position.set(40, -60, 100);
    dirLight1.castShadow = true;
    dirLight1.shadow.mapSize.width = 1024;
    dirLight1.shadow.mapSize.height = 1024;
    this.scene.add(dirLight1);

    // Luce secondaria di schiarita calda neutra (sostituito l'azzurro con bianco caldo morbido per evitare viraggi del rosso verso il rosa/magenta)
    const dirLight2 = new THREE.DirectionalLight(0xfff7ea, 0.22);
    dirLight2.position.set(-60, 50, 40);
    this.scene.add(dirLight2);

    // Luce di rimbalzo inferiore sottile
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x1a1c22, 0.18);
    this.scene.add(hemiLight);
  }

  setupBuildPlate() {
    this.buildPlateGroup = new THREE.Group();
    // Dimensioni Snapmaker U1: 270x270 mm
    const plateSize = 270;

    // Base del piatto PEI (finitura grafite/dorata opaca)
    const plateGeo = new THREE.PlaneGeometry(plateSize, plateSize);
    const plateMat = new THREE.MeshStandardMaterial({
      color: 0x181a1f,
      roughness: 0.85,
      metalness: 0.15,
    });
    this.plateMesh = new THREE.Mesh(plateGeo, plateMat);
    this.plateMesh.receiveShadow = true;
    this.plateMesh.position.set(0, 0, -0.05);
    this.buildPlateGroup.add(this.plateMesh);

    // Griglia millimetrata (griglia principale ogni 10mm, divisioni ogni 50mm)
    this.gridHelper = new THREE.GridHelper(plateSize, 27, 0x3d4352, 0x242833);
    this.gridHelper.rotation.x = Math.PI / 2;
    this.gridHelper.position.set(0, 0, 0);
    this.buildPlateGroup.add(this.gridHelper);

    // Bordo di contorno piatto
    const borderGeo = new THREE.EdgesGeometry(plateGeo);
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff3344, linewidth: 1.5 });
    this.plateBorder = new THREE.LineSegments(borderGeo, borderMat);
    this.buildPlateGroup.add(this.plateBorder);

    this.scene.add(this.buildPlateGroup);
  }

  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    if (this.modelGroup && this.modelGroup.children.length > 0) {
      this.fitCameraToObject(this.modelGroup);
    }
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Auto-fit camera al modello
   */
  fitCameraToObject(object, padding = 1.35) {
    fitCameraToObject(this.camera, object || this.modelGroup, this.controls, padding);
  }

  resolveDualColor(colorDef) {
    if (!colorDef) return null;

    const PRESETS = {
      sunset_ember: { color1: '#d9251d', color2: '#eab308' },
      '34202': { color1: '#d9251d', color2: '#eab308' },
      aurora_gold: { color1: '#0284c7', color2: '#eab308' },
      '34203': { color1: '#0284c7', color2: '#eab308' },
      solar_alloy: { color1: '#ea580c', color2: '#10b981' },
      '34204': { color1: '#ea580c', color2: '#10b981' },
      mint_lemonade: { color1: '#ECED17', color2: '#44ADE5' },
      '34205': { color1: '#ECED17', color2: '#44ADE5' },
      sea_glass: { color1: '#44ADE5', color2: '#18CCAF' },
      '34206': { color1: '#44ADE5', color2: '#18CCAF' },
      ice_lake: { color1: '#C4C7D9', color2: '#44ADE5' },
      '34207': { color1: '#C4C7D9', color2: '#44ADE5' },
      city_billboard: { color1: '#CBF914', color2: '#D623AA' },
      '34208': { color1: '#CBF914', color2: '#D623AA' }
    };

    if (typeof colorDef === 'object') {
      const sku = colorDef.sku ? String(colorDef.sku) : '';
      if (sku && PRESETS[sku]) return PRESETS[sku];

      const name = (colorDef.name || '').toLowerCase().replace(/[^a-z0-9]/g, '_');
      for (const [k, v] of Object.entries(PRESETS)) {
        if (name.includes(k)) return v;
      }

      if (colorDef.secondaryColor || colorDef.secondary_hex_color) {
        return {
          color1: colorDef.color || colorDef.hex_color || colorDef.color1 || '#d9251d',
          color2: colorDef.secondaryColor || colorDef.secondary_hex_color || colorDef.color2 || '#eab308'
        };
      }
    } else if (typeof colorDef === 'string') {
      const clean = colorDef.toLowerCase().trim();
      if (PRESETS[clean]) return PRESETS[clean];
      for (const [k, v] of Object.entries(PRESETS)) {
        if (clean.includes(k)) return v;
      }
    }
    return null;
  }

  createDualColorMaterial(color1Hex, color2Hex, wireframe = false) {
    const mat = new THREE.MeshStandardMaterial({
      roughness: 0.25,
      metalness: 0.35,
      wireframe: wireframe
    });

    mat.customProgramCacheKey = () => "dual_color_" + color1Hex + "_" + color2Hex;

    mat.onBeforeCompile = (shader) => {
      shader.uniforms.uColorA = { value: new THREE.Color(color1Hex) };
      shader.uniforms.uColorB = { value: new THREE.Color(color2Hex) };

      shader.vertexShader = `
        varying vec3 vWorldNormal;
        varying vec3 vViewDir;
      ` + shader.vertexShader;

      shader.vertexShader = shader.vertexShader.replace(
        '#include <worldpos_vertex>',
        `
        #include <worldpos_vertex>
        vWorldNormal = normalize(mat3(modelMatrix) * normal);
        vec4 worldPos = modelMatrix * vec4(transformed, 1.0);
        vViewDir = normalize(cameraPosition - worldPos.xyz);
        `
      );

      shader.fragmentShader = `
        uniform vec3 uColorA;
        uniform vec3 uColorB;
        varying vec3 vWorldNormal;
        varying vec3 vViewDir;
      ` + shader.fragmentShader;

      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <color_fragment>',
        `
        #include <color_fragment>
        // Calcola la proiezione della normale orizzontale o rispetto alla camera
        vec2 normXZ = length(vWorldNormal.xz) > 0.001 ? normalize(vWorldNormal.xz) : (length(vWorldNormal.xy) > 0.001 ? normalize(vWorldNormal.xy) : (length(vViewDir.xz) > 0.001 ? normalize(vViewDir.xz) : vec2(0.707, 0.707)));
        float angleFactor = dot(normXZ, vec2(0.707, 0.707));
        float fresnel = 0.5 + 0.5 * angleFactor;
        diffuseColor.rgb = mix(uColorA, uColorB, clamp(fresnel, 0.0, 1.0));
        `
      );
    };

    return mat;
  }

  createMaterial(colorDef, wireframe = false) {
    const dual = this.resolveDualColor(colorDef);
    if (dual) {
      return this.createDualColorMaterial(dual.color1, dual.color2, wireframe);
    }

    const hex = (typeof colorDef === 'object' && colorDef !== null) 
      ? (colorDef.color || colorDef.hex_color || '#ffffff') 
      : (colorDef || '#ffffff');

    return new THREE.MeshStandardMaterial({
      color: new THREE.Color(hex),
      roughness: 0.35,
      metalness: 0.1,
      wireframe: wireframe
    });
  }

  /**
   * Aggiorna la geometria della scena con i dati ricevuti da /api/preview
   */
  updateGeometry(previewData, palette, extruderBase, extruderText) {
    // Rimuovi mesh precedenti
    while (this.modelGroup.children.length > 0) {
      const obj = this.modelGroup.children[0];
      obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
      this.modelGroup.remove(obj);
    }
    this.partMeshes = [];

    const parts = previewData.parts || [];
    parts.forEach((p) => {
      const geom = new THREE.BufferGeometry();
      geom.setAttribute("position", new THREE.Float32BufferAttribute(p.vertices, 3));
      geom.setIndex(p.faces);
      geom.computeVertexNormals();

      // Colore/Materiale filamento associato all'estrusore (mono o dual-color)
      let ext = p.extruder;
      if (p.name && (p.name.startsWith("Icon_") || p.name.startsWith("icon_") || p.name.includes("Icon") || p.name.includes("Simbolo") || p.name.includes("simbolo"))) {
        ext = 2;
      }
      const colorDef = palette[ext] || "#ffffff";
      const mat = this.createMaterial(colorDef, this.wireframeMode);

      const mesh = new THREE.Mesh(geom, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData = { partName: p.name, extruder: ext };

      this.modelGroup.add(mesh);
      this.partMeshes.push(mesh);
    });

    // Auto-fit camera al modello generato
    if (this.partMeshes.length > 0) {
      this.fitCameraToObject(this.modelGroup);
    }
  }

  /**
   * Aggiornamento istantaneo dei soli colori (zero millisecondi, senza chiamare il server)
   */
  updateColors(palette) {
    this.partMeshes.forEach((mesh) => {
      let ext = mesh.userData.extruder;
      if (mesh.userData.partName && (mesh.userData.partName.startsWith("Icon_") || mesh.userData.partName.startsWith("icon_") || mesh.userData.partName.includes("Icon") || mesh.userData.partName.includes("Simbolo") || mesh.userData.partName.includes("simbolo"))) {
        ext = 2;
      }
      const colorDef = palette[ext];
      if (colorDef) {
        const oldMat = mesh.material;
        const newMat = this.createMaterial(colorDef, this.wireframeMode);
        mesh.material = newMat;
        if (oldMat && oldMat !== newMat) {
          oldMat.dispose();
        }
      }
    });
  }

  // Controlli Camera Preset
  resetView(productType = 'keychain') {
    if (productType === 'desk_sign') {
      this.setDeskSignView();
      return;
    }
    this.camera.position.set(0, -110, 95);
    this.controls.target.set(0, 0, 2);
    this.controls.update();
    if (this.modelGroup && this.modelGroup.children.length > 0) {
      this.fitCameraToObject(this.modelGroup);
    }
  }

  setDeskSignView() {
    const box = new THREE.Box3().setFromObject(this.modelGroup);
    const center = new THREE.Vector3(0, 0, 10);
    if (!box.isEmpty()) {
      box.getCenter(center);
    }
    // Vista frontale ergonomica (leggermente rialzata e inclinata verso il fronte della targhetta, con target al centro del testo)
    this.camera.position.set(center.x, center.y - 110, center.z + 42);
    this.controls.target.copy(center);
    this.controls.update();
    if (this.modelGroup && this.modelGroup.children.length > 0) {
      this.fitCameraToObject(this.modelGroup, 1.25);
    }
  }

  topView() {
    this.camera.position.set(0, 0, 140);
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }

  frontView() {
    this.camera.position.set(0, -140, 15);
    this.controls.target.set(0, 0, 2);
    this.controls.update();
  }

  toggleWireframe() {
    this.wireframeMode = !this.wireframeMode;
    this.partMeshes.forEach((m) => {
      m.material.wireframe = this.wireframeMode;
    });
    return this.wireframeMode;
  }

  /**
   * Cattura sincrona e affidabile dell'immagine 3D con SFONDO TRASPARENTE
   * e inquadratura prospettica 3D a 45Â° standard (isolamento modello) per la thumbnail del 3MF.
   * Restituisce una Data URL in formato image/png (RGBA 32-bit con canale alfa reale).
   */
  captureThumbnail() {
    try {
      if (!this.renderer || !this.scene || !this.camera) return null;

      // 1. Salva lo stato corrente della scena e della camera
      const savedBackground = this.scene.background;
      const savedCamPos = this.camera.position.clone();
      const savedCamTarget = this.controls ? this.controls.target.clone() : new THREE.Vector3(0, 0, 0);
      const savedPlateVis = this.buildPlateGroup ? this.buildPlateGroup.visible : true;

      // 2. Calcola Bounding Box del modello per inquadratura assonometrica 3D ottimale
      const box = new THREE.Box3().setFromObject(this.modelGroup);
      if (!box.isEmpty()) {
        const center = new THREE.Vector3();
        box.getCenter(center);
        const size = new THREE.Vector3();
        box.getSize(size);

        // Calcola la distanza camera per inquadrare perfettamente il modello con margine compatto
        const maxDim = Math.max(size.x, size.y, size.z * 3.0, 30);
        const fovRad = (this.camera.fov * Math.PI) / 180;
        const fitDistance = (maxDim / 2) / Math.tan(fovRad / 2) * 1.35;

        // Vettore di direzione assonometrico a 45Â° (inclinato da fronte-destra in alto)
        // Evidenzia lo spessore delle lettere, il contrasto dei rilievi e l'asola laterale
        const dir = new THREE.Vector3(0.35, -0.85, 0.75).normalize();
        const targetCamPos = center.clone().add(dir.multiplyScalar(fitDistance));

        this.camera.position.copy(targetCamPos);
        this.camera.lookAt(center);
        if (this.controls) {
          this.controls.target.copy(center);
          this.controls.update();
        }
      }

      // 3. Nascondi temporaneamente piatto PEI, griglia e bordo
      if (this.buildPlateGroup) {
        this.buildPlateGroup.visible = false;
      }

      // 4. Rendi completamente trasparente lo sfondo WebGL (Alpha Channel RGBA reale)
      this.scene.background = null;
      this.renderer.setClearColor(0x000000, 0.0);

      // 5. Render sincrono del solo modello 3D isolato
      this.renderer.render(this.scene, this.camera);
      const dataUrl = this.renderer.domElement.toDataURL("image/png");

      // 6. Ripristina fedelmente lo stato precedente della viewport
      this.scene.background = savedBackground;
      this.renderer.setClearColor(0x0e1014, 1.0);
      if (this.buildPlateGroup) {
        this.buildPlateGroup.visible = savedPlateVis;
      }
      this.camera.position.copy(savedCamPos);
      if (this.controls) {
        this.controls.target.copy(savedCamTarget);
        this.controls.update();
      }
      this.camera.lookAt(savedCamTarget);

      // Ri-renderizza per ripristinare il frame visibile all'utente a schermo
      this.renderer.render(this.scene, this.camera);

      if (dataUrl && dataUrl.startsWith("data:image/png;base64,")) {
        return dataUrl;
      }
      return null;
    } catch (err) {
      console.warn("Impossibile catturare thumbnail trasparente Three.js:", err);
      return null;
    }
  }
}

/**
 * Auto-fit camera Three.js al modello con padding adattivo
 * Inquadra perfettamente l'oggetto sia in orizzontale che in verticale,
 * adattandosi al fov, all'aspect ratio della finestra e alle dimensioni dell'oggetto.
 */
function fitCameraToObject(camera, object, controls, padding = 1.35) {
  if (!camera || !object) return;
  const boundingBox = new THREE.Box3().setFromObject(object);
  if (boundingBox.isEmpty()) return;
  const size = new THREE.Vector3();
  boundingBox.getSize(size);
  const center = new THREE.Vector3();
  boundingBox.getCenter(center);

  const maxDim = Math.max(size.x, size.y, size.z, 20);
  const fov = camera.fov * (Math.PI / 180);
  let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * padding;

  if (camera.aspect < 1) {
    cameraZ = cameraZ / camera.aspect;
  }

  // Direzione prospettica: se i controlli hanno un orientamento valido mantienilo, altrimenti prospettiva frontale ideale U1 (Y negativo, Z positivo)
  let direction = new THREE.Vector3(0, -0.75, 0.65).normalize();
  if (controls && controls.target && camera.position.distanceTo(controls.target) > 1) {
    const curDir = camera.position.clone().sub(controls.target);
    if (curDir.lengthSq() > 0.001) {
      direction = curDir.normalize();
    }
  }

  camera.position.copy(center).add(direction.multiplyScalar(cameraZ));

  camera.near = cameraZ / 100;
  camera.far = cameraZ * 100;
  camera.updateProjectionMatrix();

  if (controls) {
    controls.target.copy(center);
    controls.maxDistance = cameraZ * 3;
    controls.minDistance = cameraZ * 0.3;
    controls.update();
  }
}

if (typeof window !== "undefined") {
  window.fitCameraToObject = fitCameraToObject;
}

