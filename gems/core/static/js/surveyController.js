var gems = angular.module('gems');

gems.controller('surveyController', function($scope, $http){
    $scope.Surveys = {};
    $scope.queryStarted = false;
    $scope.surveySearchForm = {
        name : null,
        from : null,
        to : null
    };
    $scope.buttonEnabled = false;

    $scope.getSurveys = function getSurveys(){
        var payload = {};

        if ($scope.surveySearchForm.name != null && $scope.surveySearchForm.name != "")
        {
            payload.name = $scope.surveySearchForm.name;
        }

        if ($scope.surveySearchForm.from != null && $scope.surveySearchForm.from != "")
        {
            payload.from = $scope.surveySearchForm.from;
        }

        if ($scope.surveySearchForm.to != null && $scope.surveySearchForm.to != "")
        {
            payload.to = $scope.surveySearchForm.to;
        }

        $http({
                url: '/get_surveys/',
                method: 'POST',
                data: payload
            })
            .success(function(data){
                alert(data);
                $scope.Surveys = data;
            })
            .error(function(data){
                alert("Failed to retreive the surveys");
            });
    };

});