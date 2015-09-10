var gems = angular.module('gems');

gems.controller('groupController', function($scope, $http){
    $scope.groupName = $scope.getGroupName();
    $scope.queryStarted = false;
    $scope.numberOfRows = 0;
    $scope.rows = [];
    $scope.columns = [];

    $scope.filteredGroups = [];
    $scope.pagedGroups = [];
    $scope.currentPage = 1;
    $scope.maxSize = 6;
    $scope.buttonText = "Display Results";
    $scope.queryDone = true;
    $scope.showAllResults = false;
    $scope.dispCol = {
        hide: false
    };

    $scope.fetchResults = function fetchResults(){
        $scope.rows = [];
        $scope.queryStarted = true;
        $scope.queryDone = false;
        $scope.buttonText = "Loading Results";
        var payload = {};

        if($scope.numberOfRows != null && $scope.numberOfRows > 0){
            payload.limit = $scope.numberOfRows;
        }

        payload.filters = $scope.filters
        $scope.columns = $scope.origColumns.slice();

        for(var x = 0; x < $scope.columns.length; ++x){
            if(x > 3){
                $scope.columns[x].noHide = false;
                $scope.columns[x].hide = true;
            }
            else{
                $scope.columns[x].noHide = true;
                $scope.columns[x].hide = false;
            }
        }

        $http({
            url: '/query/',
            method: 'POST',
            data: payload
            })
            .then(function(data){
                var results = data.data;

                var retVal = $scope.processQueryResults(results, $scope.columns);
                $scope.columns = retVal[0];
                $scope.rows = retVal[1];

                if ($scope.queryStarted == true){
                        $scope.buttonText = "Refresh Results";
                }else{
                    $scope.buttonText = "Display Results";
                }

                $scope.queryDone = true;
                $scope.currentPage = 0;
                $scope.pagedGroups = $scope.groupToPages($scope.rows);
            })
    };

    $scope.selectRow = function selectRow(index){
        $scope.rows[index].selected = true;
    };

    $scope.selectFunction = function selectFunction(){
        if($scope.allRowsSelected()){
            // deselect all rows
            for(var x = 0; x < $scope.rows.length; ++x){
                $scope.rows[x].selected = false;
            }
        } else {
            // select all rows
            for(var x = 0; x < $scope.rows.length; ++x){
                $scope.rows[x].selected = true;
            }
        }
    };

    $scope.allRowsSelected = function allRowsSelected(){
        var retVal = true;

        for(var x = 0; x < $scope.rows.length; ++x){
            retVal = retVal && $scope.rows[x].selected;
        }

        return retVal;
    };

    $scope.anyRowsSelected = function anyRowsSelected(){
        var retVal = false;

        for(var x = 0; x < $scope.rows.length; ++x){
            retVal = retVal || $scope.rows[x].selected;
        }

        return retVal;
    };

    $scope.getGroup = function getGroup(filters){
        var group = {
            name: $scope.groupName,
            members: [],
            query_words: $scope.getQueryWords(),
            filters: JSON.stringify( filters )
        };

        var contactIndex = 0;

        for(var x = 0; x < $scope.fields.length; ++x){
            if($scope.fields[x].name === 'contact' ){
                contactIndex = x;
                break;
            }
        }

        for(var x = 0; x < $scope.rows.length; ++x){
            if($scope.rows[x].selected){
                group.members.push($scope.rows[x].fields[contactIndex]);
            }
        }

        return group;
    };

    $scope.saveGroup = function saveGroup(filters, group, count){
        group = typeof group !== 'undefined' ? group : $scope.getGroup(filters);
        count = typeof count !== 'undefined' ? count : 3;

        $http.post('/create_contactgroup/', group, config={timeout: 300000}).
            success(function(status){
                $scope.showAlert('alert-success', 'Success', status);
            }).
            error(function(data, status){
                if(count === 0){
                    $scope.showAlert('alert-warning', 'Failed', 'Failed to create contact group after 3 retries.' + '\n\n' + status + ' : ' + data);
                } else {
                    // retry
                    $scope.saveGroup(filters, group, count - 1);
                }

            });

        $scope.cancel();
    };

    //need group_key
    $scope.updateGroup = function updateGroup(filters){
        var group = $scope.getGroup(filters);
        group.group_key = $scope.groupKey;

        $http.post('/update_contactgroup/', group).
            success(function(status){
                $scope.showAlert('alert-success', 'Success', status);
            }).
            error(function(status){
                $scope.showAlert('alert-warning', 'Failed', 'Failed to update contact group.'  + '\n\n' + status);
            });

        $scope.cancel();
    };

    ///////PAGING/////
    $scope.groupToPages = function(results){
        var paged = [];
        var temp = results.slice();
        while (temp.length > 0)
        {
            paged.push(temp.splice(0, $scope.itemsPerPage));
        }
        return paged;
    };

    $scope.setPage = function (){
        $scope.currentPage = this.n;
    };

    $scope.cancel = function cancel(){
        $scope.hideCreateContact();
    };

    $scope.$watch('$parent.createGroup', function(newValue, oldValue){
        if(newValue){
            $scope.groupName = $scope.getGroupName();
        }
    });

    $scope.queryValid = function queryValid(){
        return $scope.getQueryValid();
    }

    $scope.toggleShowAllResults = function toggleShowAllResults(){
        $scope.showAllResults = !$scope.showAllResults;

        for(var x = 0; x < $scope.columns.length; ++x){
            if(!$scope.columns[x].noHide){
                $scope.columns[x].hide = !$scope.columns[x].hide;
            }
        }
    }
});
