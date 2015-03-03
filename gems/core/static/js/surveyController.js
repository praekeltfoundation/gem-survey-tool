var gems = angular.module('gems');

gems.controller('surveyController', function($scope, $http){
    $scope.Surveys = {};
    $scope.queryStarted = false;
    $scope.surveySearchForm = {
        name : null,
        from : null,
        to : null
    };

    $scope.getSurveys = function getSurveys(){
        $scope.queryStarted = true;
        var payload = {};

        if (!!$scope.surveySearchForm.name)
        {
            payload.name = $scope.surveySearchForm.name;
        }

        if (!!$scope.surveySearchForm.from)
        {
            payload.from = $scope.surveySearchForm.from;
        }

        if (!!$scope.surveySearchForm.to)
        {
            payload.to = $scope.surveySearchForm.to;
        }

        $http({
                url: '/get_surveys/',
                method: 'POST',
                data: payload
            })
            .success(function(data){
                $scope.Surveys = data;
            })
            .error(function(data){
                alert("Failed to retreive the surveys");
            });
    };

});