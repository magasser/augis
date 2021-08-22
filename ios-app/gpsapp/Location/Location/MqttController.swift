//
//  MqttController.swift
//  Location
//
//  Created by Julian Haldimann on 06.03.21.
//  Copyright © 2021 Julian Haldimann. All rights reserved.
//

import Foundation
import CocoaMQTT
import UIKit


class MqttController: CocoaMQTTDelegate{
    public var client:CocoaMQTT!
    
    let defaults = UserDefaults.standard
    let clientID = "CocoaMQTT-" + String(ProcessInfo().processIdentifier)
    var host:String
    var mqttRaspConn:Bool
    
    var responseMessages: [String: ((_ topic:String,_ data: String?) -> Void)?] = ["augis/raspberry/ip":nil]
    
    init() {
        self.host = defaults.string(forKey: "mqttServer") ?? "augis.ti.bfh.ch";
        self.mqttRaspConn = false;
    }
    
    // Create a connection from the phone to the broker
    func connect() {
        print("Connecting to MQTT on \(self.host)")
        client = CocoaMQTT(clientID: clientID, host: self.host, port: 1883);
        client.autoReconnect = true;
        client.cleanSession = true;
        client.username = "user";
        client.password = "Augis2020$";
        client.keepAlive = 60;
        client.delegate = self;
        
        client.didReceiveMessage = { mqtt, message, id in
            print("Message received in topic \(message.topic) with payload \(message.string!)");
        }
        
        _ = client.connect()
    }
    
    func disconnect() {
        client.disconnect()
    }
    
    func changeHost(newHost: String) {
        self.host = newHost;
        self.disconnect();
        self.connect();
    }
}

extension MqttController {
    // If a specific Topic is subscribed
    func mqtt(_ mqtt: CocoaMQTT, didSubscribeTopics success: NSDictionary, failed: [String]) {
        debugPrint("Subscribe");
    }
    
    // If a specific Topic is unsubscribed
    func mqtt(_ mqtt: CocoaMQTT, didUnsubscribeTopics topics: [String]) {
        debugPrint("subscribed");
    }
    
    // The acknowledgment for a connection
    func mqtt(_ mqtt: CocoaMQTT, didConnectAck ack: CocoaMQTTConnAck) {
        print("ack: \(ack)")
        
        if ack == .accept {
            for topic in responseMessages {
                mqtt.subscribe(topic.key)
            }
        }
    }
    
    // When the client change from a state to another
    func mqtt(_ mqtt: CocoaMQTT, didStateChangeTo state: CocoaMQTTConnState) {
        print("new state: \(state)")
    }
    
    // When a message was published
    func mqtt(_ mqtt: CocoaMQTT, didPublishMessage message: CocoaMQTTMessage, id: UInt16) {
        //print("message: \(message.string.debugDescription), id: \(id)")
    }
    
    // The acknowledgment for a publish call
    func mqtt(_ mqtt: CocoaMQTT, didPublishAck id: UInt16) {
        //print("id: \(id)")
    }
    
    // Callback for a received Message
    func mqtt(_ mqtt: CocoaMQTT, didReceiveMessage message: CocoaMQTTMessage, id: UInt16 ) {
        print("message: \(message.topic), id: \(id)")
        
        if let delegate = responseMessages[message.topic] {
            delegate?(message.topic, message.string)
        }
        
        switch message.topic {
            case "augis/raspberry/ip":
                if (!self.mqttRaspConn) {
                    self.changeHost(newHost: message.string!)
                    self.mqttRaspConn = true;
                }
            default:
                print(message.topic);
        }
    }
    
    // Callback if the client subscribe a new topic
    func mqtt(_ mqtt: CocoaMQTT, didSubscribeTopic topic: String) {
        print("topic: \(topic)")
    }
    
    // Callback if the client unsubscribe a new topic
    func mqtt(_ mqtt: CocoaMQTT, didUnsubscribeTopic topic: String) {
        print("topic: \(topic)")
    }
    
    // Ping Message
    func mqttDidPing(_ mqtt: CocoaMQTT) {
        print("Ping")
    }
    
    // Pong Message
    func mqttDidReceivePong(_ mqtt: CocoaMQTT) {
        print("Pong")
    }
    
    // Disconnect due to an error
    func mqttDidDisconnect(_ mqtt: CocoaMQTT, withError err: Error?) {
        print("\(err.debugDescription)")
    }
}
