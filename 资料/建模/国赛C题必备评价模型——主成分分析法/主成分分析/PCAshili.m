%  PCA步骤：
% 
% （1）对原始数据进行标准化处理
% 
% （2）计算样本相关系数矩阵
% 
% （3）计算相关系数矩阵R的特征值和相应的特征向量
% 
% （4）选择重要的主成分，写出主成分表达式
% 
%  下例中企业综合实力排序问题，其中各列分别为：
%  企业序号；净利润率；固定资产利润率；总产值利润率；销售收入利润率；产品成本利润率；物耗利润率；人均利润；流动资金
load b.txt
A=b;
a=size(A,1);                                        % 获得矩阵A的行数
b=size(A,2);                                        % 获得矩阵A的列数
for i=1:8
    SA(:,i)=(A(:,i)-mean(A(:,i)))/std(A(:,i));      % std函数是用来求向量的标准差
end
% 计算相关系数矩阵的特征值和特征向量
CM=corrcoef(SA);                                    % 计算相关系数矩阵
[V,D]=eig(CM);                                      % 计算特征值和特征向量
for j=1:b
    DS(j,1)=D(b+1-j,b+1-j);                         % 对特征值按降序排列
end
for i=1:b
    DS(i,2)=DS(i,1)/sum(DS(:,1));                   % 贡献率
    DS(i,3)=sum(DS(1:i,1))/sum(DS(:,1));            % 累计贡献率
end
% 选择主成分及对应的特征向量
T=0.9;                                              % ！！！主成分信息保留率，手动设置
for k=1:b
    if DS(k,3)>=T
        Com_num=k;
        break;
    end
end
% 提取主成分对应的特征向量
for j=1:Com_num
    PV(:,j)=V(:,b+1-j);
end
% 计算各评价对象的主成分得分
new_score=SA*PV;
for i=1:a
    total_score(i,1)=sum(new_score(i,:));
    total_score(i,2)=i; %#ok<*SAGROW>
end
result_report=[new_score,total_score];               % 将各主成分得分与总分放在同一个矩阵中
result_report=sortrows(result_report,-5);            % 按总分降序排序
% 输出模型及结果报告
disp('特征值及其贡献率，累加贡献率：')
DS %#ok<*NOPTS>
disp('信息保留率T对应的主成分数与特征向量：')
Com_num
PV
disp('主成分得分及排序（按第5列的总分进行排序，前4列为各主成分得分，第6列为企业编号）')
result_report