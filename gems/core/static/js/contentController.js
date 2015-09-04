var gems = angular.module('gems');

gems.controller('contentController', function ($scope, $http, $filter) {
    $scope.ContactGroups = {};

    $scope.group_id;

    $scope.sorting = {
        order: 'name',
        reverse: {
            name: false,
            createdOn: false,
            rules: false
        }
    }

    $scope.filteredGroups = [];
    $scope.pagedGroups = [];
    $scope.currentPage = 1;
    $scope.itemsPerPage = 10;
    $scope.maxSize = 6;

    $scope.setGroupId =  function setGroupId(id){
        $scope.group_id = id;
    }

    $scope.getContactGroups = function getContactGroups() {
        $http.get('/contactgroup/').
            success(function(data) {
                $scope.ContactGroups = data;
                $scope.search();
            }).
            error(function(data) {
                alert("failed to retreive data.");
            });
    };

    $scope.deleteContactGroup = function deleteContactGroup(){
        $http.post('/delete_contactgroup/', {group_id : $scope.group_id}).
            success(function(status){
                if(status  == "FAILED")
                    alert("Failed to delete.");
                $scope.getContactGroups();
            }).
            error(function(status){
                alert("Failed to delete.");
            });
    };

    $scope.createContactGroup = function createContactGroup(g_name){
        $http.post('/create_contactgroup/', {group_name : g_name}).
            success(function(status){
                alert(status);
            }).
            error(function(status){
                alert("failed"  + status);
            });
    };

        var searchMatch = function (haystack, needle){
        if (!needle){
            return true;
        }
        return haystack.toLowerCase().indexOf(needle.toLowerCase()) !== -1;
    };

    $scope.search = function() {
        $scope.filteredGroups = $filter('filter')($scope.ContactGroups, function(item){
            for(var attr in item){
                if(searchMatch(item[attr], $scope.query))
                    return true;
            }
            return false;
        });

        if ($scope.sorting.order !== '') {
            $scope.filteredGroups = $filter('orderBy')($scope.filteredGroups, $scope.sorting.order, $scope.sorting.reverse[$scope.sorting.order]);
        }
        $scope.currentPage = 0;
        $scope.groupToPages();
    };

    $scope.groupToPages = function(){
        $scope.pagedGroups = [];

        for (var i = 0; i < $scope.filteredGroups.length; i++){
            if (i % $scope.itemsPerPage === 0){
                $scope.pagedGroups[Math.floor(i / $scope.itemsPerPage)] = [ $scope.filteredGroups[i] ];
            }else{
                $scope.pagedGroups[Math.floor(i / $scope.itemsPerPage)].push($scope.filteredGroups[i]);
            }
        }
    };

    $scope.range = function (start, end){
        var ret = [];
        if (!end){
            end = start;
            start = 0;
        }
        for (var i = start; i < end; i++){
            ret.push(i);
        }
        return ret;
    };

    $scope.prevPage = function (){
        if ($scope.currentPage > 0){
            $scope.currentPage--;
        }
    };

    $scope.nextPage = function (){
        if ($scope.currentPage < $scope.pagedItems.length - 1){
            $scope.currentPage++;
        }
    };

    $scope.setPage = function (){
        $scope.currentPage = this.n;
    };

    $scope.getContactGroups();
});