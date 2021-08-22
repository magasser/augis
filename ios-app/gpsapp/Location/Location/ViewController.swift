//
//  ViewController.swift
//  Location
//
//  Created by Julian Haldimann on 20.10.20.
//  Updated by Julian Haldimann on 13.03.21
//  Copyright © 2020 Julian Haldimann. All rights reserved.
//

import UIKit
import CoreLocation
import CocoaMQTT
import CoreMotion

class ViewController: UIViewController, CLLocationManagerDelegate, UITextFieldDelegate {
    var motionManager = CMMotionManager()
    
    var timer: Timer!
    
    // Create new Instance of MQTT Controller
    let mqtt = MqttController()
    var oldDir = 0

    // Output Labels to display Data
    @IBOutlet var labelCoordinates: UILabel!
    @IBOutlet var outputlong: UITextField!
    @IBOutlet var outputlat: UITextField!
    @IBOutlet var outputCompass: UITextField!
    @IBOutlet var outputX: UITextField!
    @IBOutlet var outputY: UITextField!
    @IBOutlet var outputZ: UITextField!
    @IBOutlet var outputAX: UITextField!
    @IBOutlet var outputAY: UITextField!
    @IBOutlet var outputAZ: UITextField!
    
    var manager: CLLocationManager?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Make a small delay at start
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {}
        
        // Connect to Mqtt Broker
        mqtt.connect()
        sleep(1)
        motionManager.startAccelerometerUpdates()
        motionManager.startGyroUpdates()
        motionManager.startMagnetometerUpdates()
        motionManager.startDeviceMotionUpdates()
        timer = Timer.scheduledTimer(timeInterval: 1, target: self, selector: #selector(ViewController.update), userInfo: nil, repeats: true)
    }
    
    @objc func appTerminate() {
        mqtt.disconnect()
    }
    
    @IBAction func didTabButton() {
        guard let vc = storyboard?.instantiateViewController(identifier: "mapVC") as? MapViewController else {
            return
        }
        
        present(vc, animated: true)
    }
    
    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        // Default values
        manager = CLLocationManager()
        outputlat.delegate = self
        outputlong.delegate = self
        
        // Manager is used to get information of Location and Heading
        manager?.delegate = self
        manager?.desiredAccuracy = kCLLocationAccuracyBest
        manager?.requestWhenInUseAuthorization()
        manager?.startUpdatingLocation()
        manager?.startUpdatingHeading()
    }
    
    @objc func update() {
        
        if motionManager.isGyroAvailable {
            motionManager.deviceMotionUpdateInterval = 1;
            motionManager.startDeviceMotionUpdates()

            motionManager.gyroUpdateInterval = 1
            guard let currentQueue = OperationQueue.current else { return }
            motionManager.startGyroUpdates(to: currentQueue) { [self] (gyroData, error) in

                // Do Something, call function, etc
                if let rotation = gyroData?.rotationRate {
                    
                    outputAX.text = "\(rotation.x)"
                    outputAY.text = "\(rotation.y)"
                    outputAZ.text = "\(rotation.z)"
                    
                    self.mqtt.client.publish("augis/sensor/gyro", withString: "\(rotation.x)" + "," + "\(rotation.y)" + "," +  "\(rotation.z)")
                }
            }
        }
        
        
        if let accelerometerData = motionManager.accelerometerData {
            let x = accelerometerData.acceleration.x * 9.81
            let y = accelerometerData.acceleration.y * 9.81
            let z = accelerometerData.acceleration.z * 9.81
            
            outputX.text = "\(x)"
            outputY.text = "\(y)"
            outputZ.text = "\(z)"
            
            self.mqtt.client.publish("augis/sensor/accel", withString: "\(x)" + "," + "\(y)" + "," +  "\(z)")
           }
       }
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {

        guard let first = locations.first else {
            return
        }
        
        // Print the actual position into the textfields
        outputlat.text = "\(first.coordinate.latitude)"
        outputlong.text = "\(first.coordinate.longitude)"
        
        
        // Publish the data from the sensor to the mqtt broker
        let payload = "\(first.coordinate.latitude)" + "," + "\(first.coordinate.longitude)"
        mqtt.client.publish("augis/sensor/gps/phone", withString: payload)
    }
    
    func locationManager(_ manager: CLLocationManager, didUpdateHeading newHeading: CLHeading) {
        // Print out the actual direction of the device
        outputCompass.text = "\((newHeading.magneticHeading * 100).rounded() / 100)";
        
        mqtt.client.publish("augis/sensor/heading", withString: "\((newHeading.magneticHeading * 100).rounded() / 100)")
    }
    
    /**
     This function can be used to calculate the distance between two decimal coordinates

     - parameter lat1: Latitude of the first coordinate.
     - parameter long1: Longitude of the first  coordinate.
     - parameter lat2: Latitude of the second coordinate.
     - parameter long2: Longitude of the second coordinate.
     */
    func calcDistance(lat1: Double, long1: Double, lat2: Double, long2: Double) -> Double {
        let radius = 6371.0
        
        // Convert all radians to degrees
        let dLat = degreesToRadians(lat1 - lat2)
        let dLon = degreesToRadians(long1 - long2)
        let tmplat1 = degreesToRadians(lat1)
        let tmplat2 = degreesToRadians(lat2)
        
        let a = sin(dLat / 2) * sin(dLat/2) + sin(dLon / 2) * sin(dLon / 2) * cos(tmplat1) * cos(tmplat2)
        
        let c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return radius * c * 1000.0
    }
    
    /**
     This function can be used to calculate the angle between two decimal coordinates

     - parameter lat1: Latitude of the first coordinate.
     - parameter long1: Longitude of the first  coordinate.
     - parameter lat2: Latitude of the second coordinate.
     - parameter long2: Longitude of the second coordinate.
     */
    func calcAngle(lat1: Double, long1: Double, lat2: Double, long2: Double) {
        // Convert all radians to degrees
        let dLon = degreesToRadians(long2 - long1)
        let latdest = degreesToRadians(lat2)
        let latpos = degreesToRadians(lat1)
        
        let x = cos(latdest) * sin(dLon)
        let y = cos(latpos) * sin(latdest) - sin(latpos) * cos(latdest) * cos(dLon)
        
        // Calculate the direction in radian
        let bearing = atan2(x, y)
    }
    
    /**
     This function can be used to convert a degree value to a radian value

     - parameter val: Degrees to convert
     - returns: Degrees as a double
     */
    let degreesToRadians = {(val: Double) -> Double in
        return val * .pi / 180
    }
    
    /**
     This function can be used to convert a radian value to a degree value

     - parameter val: Degrees to convert
     - returns: Radian as a double
     */
    let radiansToDegrees = {(val: Double) -> Double in
        return val * 180 / .pi
    }
    
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
       // Try to find next responder
       if let nextField = textField.superview?.viewWithTag(textField.tag + 1) as? UITextField {
          nextField.becomeFirstResponder()
       } else {
          // Not found, so remove keyboard.
          textField.resignFirstResponder()
       }
       // Do not add a line break
       return false
    }
}
