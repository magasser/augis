//
//  MapViewController.swift
//  Location
//
//  Created by Julian Haldimann on 22.10.20.
//  Copyright © 2020 Julian Haldimann. All rights reserved.
//

import MapKit
import UIKit

class MapViewController: UIViewController {
    var inputLat = ""
    var inputLong = ""
    @IBOutlet var mapView: MKMapView!
    let vc = ViewController()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        let london = MKPointAnnotation()
        london.title = inputLat
        london.coordinate = CLLocationCoordinate2D(latitude: Double(inputLat) ?? 0.0, longitude: Double(inputLong) ?? 0.0)
        mapView.addAnnotation(london)
    }

    func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
        guard annotation is MKPointAnnotation else { return nil }

        let identifier = "Annotation"
        var annotationView = mapView.dequeueReusableAnnotationView(withIdentifier: identifier)

        if annotationView == nil {
            annotationView = MKPinAnnotationView(annotation: annotation, reuseIdentifier: identifier)
            annotationView!.canShowCallout = true
        } else {
            annotationView!.annotation = annotation
        }

        return annotationView
    }

}
