// ============================================================
// COMPLETE WORKING camera.js - Assignment 4
// ============================================================

class Camera {
    constructor() {
      this.fov = 60;
      this.eye = new Vector3([16, 1.6, 16]);  // Start in middle of world
      this.at = new Vector3([16, 1.6, 15]);   // Look forward
      this.up = new Vector3([0, 1, 0]);       // Up is +Y
      
      this.viewMatrix = new Matrix4();
      this.projectionMatrix = new Matrix4();
      
      this.speed = 0.2;
      this.rotationSpeed = 3;
      
      this.alpha = 0;  // Horizontal rotation
      this.beta = 0;   // Vertical rotation
      
      this.updateViewMatrix();
      this.updateProjectionMatrix();
    }
    
    updateViewMatrix() {
      this.viewMatrix.setLookAt(
        this.eye.elements[0], this.eye.elements[1], this.eye.elements[2],
        this.at.elements[0], this.at.elements[1], this.at.elements[2],
        this.up.elements[0], this.up.elements[1], this.up.elements[2]
      );
    }
    
    updateProjectionMatrix() {
      this.projectionMatrix.setPerspective(
        this.fov, 
        canvas.width / canvas.height, 
        0.1, 
        1000
      );
    }
    
    moveForward() {
      let f = new Vector3();
      f.set(this.at);
      f.sub(this.eye);
      f.normalize();
      f.mul(this.speed);
      
      this.eye.add(f);
      this.at.add(f);
      this.updateViewMatrix();
    }
    
    moveBackward() {
      let b = new Vector3();
      b.set(this.eye);
      b.sub(this.at);
      b.normalize();
      b.mul(this.speed);
      
      this.eye.add(b);
      this.at.add(b);
      this.updateViewMatrix();
    }
    
    moveLeft() {
      let f = new Vector3();
      f.set(this.at);
      f.sub(this.eye);
      
      let s = Vector3.cross(this.up, f);
      s.normalize();
      s.mul(this.speed);
      
      this.eye.add(s);
      this.at.add(s);
      this.updateViewMatrix();
    }
    
    moveRight() {
      let f = new Vector3();
      f.set(this.at);
      f.sub(this.eye);
      
      let s = Vector3.cross(f, this.up);
      s.normalize();
      s.mul(this.speed);
      
      this.eye.add(s);
      this.at.add(s);
      this.updateViewMatrix();
    }
    
    panLeft() {
      let f = new Vector3();
      f.set(this.at);
      f.sub(this.eye);
      
      let rotationMatrix = new Matrix4();
      rotationMatrix.setRotate(
        this.rotationSpeed, 
        this.up.elements[0], 
        this.up.elements[1], 
        this.up.elements[2]
      );
      
      let f_prime = rotationMatrix.multiplyVector3(f);
      
      this.at.set(this.eye);
      this.at.add(f_prime);
      this.updateViewMatrix();
    }
    
    panRight() {
      let f = new Vector3();
      f.set(this.at);
      f.sub(this.eye);
      
      let rotationMatrix = new Matrix4();
      rotationMatrix.setRotate(
        -this.rotationSpeed, 
        this.up.elements[0], 
        this.up.elements[1], 
        this.up.elements[2]
      );
      
      let f_prime = rotationMatrix.multiplyVector3(f);
      
      this.at.set(this.eye);
      this.at.add(f_prime);
      this.updateViewMatrix();
    }
    
    rotate(deltaX, deltaY) {
      this.alpha -= deltaX * 0.3;
      this.beta += deltaY * 0.2;
      this.beta = Math.max(-89, Math.min(89, this.beta));
      
      let alphaRad = this.alpha * Math.PI / 180;
      let betaRad = this.beta * Math.PI / 180;
      
      let forward = new Vector3([
        Math.cos(betaRad) * Math.sin(alphaRad),
        Math.sin(betaRad),
        Math.cos(betaRad) * Math.cos(alphaRad)
      ]);
      
      this.at.set(this.eye);
      this.at.add(forward);
      this.updateViewMatrix();
    }
  }