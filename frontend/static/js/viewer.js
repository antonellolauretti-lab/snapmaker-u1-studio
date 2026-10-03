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
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.renderer.domElement.style.touchAction = "none";
    this.container.appendChild(this.renderer.domElement);

    // 4. OrbitControls Touch-friendly
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.02; // Impedisce di andare sotto al piatto
    this.controls.minDistance = 20;
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
    // Luce d'ambiente soffusa
    const ambient = new THREE.AmbientLight(0xffffff, 0.55);
    this.scene.add(ambient);

    // Luce primaria superiore frontale (esalta il rilievo)
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.85);
    dirLight1.position.set(40, -60, 100);
    dirLight1.castShadow = true;
    dirLight1.shadow.mapSize.width = 1024;
    dirLight1.shadow.mapSize.height = 1024;
    this.scene.add(dirLight1);

    // Luce secondaria morbida dal lato opposto
    const dirLight2 = new THREE.DirectionalLight(0xa5c4ff, 0.4);
    dirLight2.position.set(-60, 50, 40);
    this.scene.add(dirLight2);

    // Luce di rimbalzo inferiore sottile
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x22242a, 0.3);
    this.scene.add(hemiLight);
  }

  setupBuildPlate() {
    // Dimensioni Snapmaker U1: 270x270 mm
    const plateSize = 270;

    // Base del piatto PEI (finitura grafite/dorata opaca)
    const plateGeo = new THREE.PlaneGeometry(plateSize, plateSize);
    const plateMat = new THREE.MeshStandardMaterial({
      color: 0x181a1f,
      roughness: 0.85,
      metalness: 0.15,
    });
    const plateMesh = new THREE.Mesh(plateGeo, plateMat);
    plateMesh.receiveShadow = true;
    plateMesh.position.set(0, 0, -0.05);
    this.scene.add(plateMesh);

    // Griglia millimetrata (griglia principale ogni 10mm, divisioni ogni 50mm)
    const gridHelper = new THREE.GridHelper(plateSize, 27, 0x3d4352, 0x242833);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.set(0, 0, 0);
    this.scene.add(gridHelper);

    // Bordo di contorno piatto
    const borderGeo = new THREE.EdgesGeometry(plateGeo);
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff3344, linewidth: 1.5 });
    const border = new THREE.LineSegments(borderGeo, borderMat);
    this.scene.add(border);
  }

  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Aggiorna la geometria della scena con i dati ricevuti da /api/preview
   */
  updateGeometry(previewData, palette, extruderBase, extruderText) {
    // Rimuovi mesh precedenti
    while (this.modelGroup.children.length > 0) {
      const obj = this.modelGroup.children[0];
      obj.geometry.dispose();
      obj.material.dispose();
      this.modelGroup.remove(obj);
    }
    this.partMeshes = [];

    const parts = previewData.parts || [];
    parts.forEach((p) => {
      const geom = new THREE.BufferGeometry();
      geom.setAttribute("position", new THREE.Float32BufferAttribute(p.vertices, 3));
      geom.setIndex(p.faces);
      geom.computeVertexNormals();

      // Colore filamento associato all'estrusore
      const colorHex = palette[p.extruder] || "#ffffff";
      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(colorHex),
        roughness: 0.38,
        metalness: 0.08,
        wireframe: this.wireframeMode,
      });

      const mesh = new THREE.Mesh(geom, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData = { partName: p.name, extruder: p.extruder };

      this.modelGroup.add(mesh);
      this.partMeshes.push(mesh);
    });
  }

  /**
   * Aggiornamento istantaneo dei soli colori (zero millisecondi, senza chiamare il server)
   */
  updateColors(palette) {
    this.partMeshes.forEach((mesh) => {
      const ext = mesh.userData.extruder;
      if (palette[ext]) {
        mesh.material.color.set(palette[ext]);
      }
    });
  }

  // Controlli Camera Preset
  resetView() {
    this.camera.position.set(0, -110, 95);
    this.controls.target.set(0, 0, 2);
    this.controls.update();
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
}
