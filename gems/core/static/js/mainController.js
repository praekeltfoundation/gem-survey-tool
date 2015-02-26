var gems = angular.module('gems');

gems.controller('mainController', function($scope, $http){
    $scope.showSurveyDataMenu = false;
    $scope.showContactMenu = false;
    $scope.showCreateContact = false;

    $scope.toggleSurveyDataMenu = function toggleSurveyDataMenu(){
        $scope.showSurveyDataMenu = !$scope.showSurveyDataMenu;

        if($scope.showSurveyDataMenu == true){
            $scope.showContactMenu = false;
        }
    };

    $scope.toggleContactMenu = function toggleContactMenu(){
        $scope.showContactMenu = !$scope.showContactMenu;

        if($scope.showContactMenu == true){
            $scope.showSurveyDataMenu = false;
        }
    };
});
