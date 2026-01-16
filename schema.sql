CREATE TABLE IF NOT EXISTS `todolist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `title` varchar(1024) NOT NULL,
  `status` int(2) NOT NULL COMMENT '是否完成',
  `create_time` int(11) NOT NULL,
  `category` varchar(50) NOT NULL DEFAULT '生活' COMMENT '分类',
  `priority` int(2) NOT NULL DEFAULT 2 COMMENT '优先级',
  `deadline` int(11) DEFAULT NULL COMMENT '截止时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

insert into todolist(id, user_id, title, status, create_time, category, priority) values(1, 1, '习近平五谈稳中求进织密扎牢民生保障网', '0', 1482214350, '工作', 0), (2, 1, '特朗普获超270张选举人票将入主白 宫', '1', 1482214350, '生活', 2);


CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(24) DEFAULT NULL,
  `password` varchar(24) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

insert into user values(1, 'admin', 'admin');
