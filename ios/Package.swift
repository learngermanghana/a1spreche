// swift-tools-version: 6.1
import PackageDescription

let package = Package(
    name: "AuthViewModelPackage",
    products: [
        .library(name: "AuthViewModelModule", targets: ["AuthViewModelModule"]),
    ],
    targets: [
        .target(
            name: "AuthViewModelModule",
            path: ".",
            sources: ["AuthViewModel.swift"]
        ),
        .testTarget(
            name: "AuthViewModelTests",
            dependencies: ["AuthViewModelModule"],
            path: "Tests"
        ),
    ]
)
